from statsmodels.tsa.holtwinters import ExponentialSmoothing
import numpy as np
from django.db.models import Q
from datetime import date
from dateutil import relativedelta
from finance.models import Transaction

def advanced_forecast(series, periods=3):
    """Удосконалений метод прогнозування з використанням трійного експоненціального згладжування"""
    try:
        model = ExponentialSmoothing(
            series,
            trend='add',
            seasonal='add',
            seasonal_periods=3
        ).fit()
        return model.forecast(periods).tolist()
    except:
        # Резервний метод для коротких рядів
        last_value = series[-1]
        trend = np.mean(np.diff(series[-3:])) if len(series) >= 3 else 0
        return [last_value + (i + 1) * trend for i in range(periods)]


def analyze_trends(user, months_back=12, forecast_months=3):
    today = date.today()
    months = [(today - relativedelta(months=i)).replace(day=1)
              for i in reversed(range(1, months_back + 1))]

    # Отримання даних з урахуванням валют
    transactions = Transaction.objects.filter(
        Q(user=user),
        Q(type='expense'),
        Q(date__gte=months[0]),
        Q(date__lt=today),
        ~Q(category__name__icontains='переказ')
    ).select_related('category', 'account')

    # Обробка даних
    category_data = {}
    for tx in transactions:
        key = (tx.category.name, tx.account.currency.code if tx.account.currency else 'UAH')
        if key not in category_data:
            category_data[key] = {
                'values': [0] * months_back,
                'count': 0,
                'months': months.copy()
            }
        month_idx = (tx.date.year - months[0].year) * 12 + (tx.date.month - months[0].month)
        if 0 <= month_idx < months_back:
            category_data[key]['values'][month_idx] += float(tx.amount)
            category_data[key]['count'] += 1

    # Аналіз і прогнозування
    results = []
    for (category, currency), data in category_data.items():
        if data['count'] < 3 or sum(data['values']) < 500:
            continue

        values = data['values']
        non_zero = [v for v in values if v > 0]

        if len(non_zero) < 3:
            continue

        # Виявлення тренду
        trend_coef = calculate_trend_coefficient(values)
        forecast = advanced_forecast(non_zero, forecast_months)

        # Генерація рекомендацій
        insight = generate_advanced_insight(
            category=category,
            values=values,
            forecast=forecast,
            currency=currency,
            trend_coef=trend_coef
        )

        results.append({
            'category': f"{category} ({currency})",
            'values': values,
            'months': data['months'],
            'forecast': forecast,
            'insight': insight,
            'trend_coef': trend_coef,
            'currency': currency
        })

    return sorted(results, key=lambda x: abs(x['trend_coef']), reverse=True)[:10]


def generate_advanced_insight(category, values, forecast, currency, trend_coef):
    """Генерує персоналізовані рекомендації з прогнозом"""
    last_value = next((v for v in reversed(values) if v > 0), 0)
    avg = sum(values) / len([v for v in values if v > 0])

    if trend_coef > 0.2:
        action = "зростають"
        suggestion = "Рекомендуємо переглянути витрати цієї категорії"
    elif trend_coef < -0.2:
        action = "знижуються"
        suggestion = "Можливо, ви знайшли ефективніший спосіб витрат"
    else:
        action = "стабільні"
        suggestion = "Порівняйте з аналогічними категоріями для оптимізації"

    forecast_text = ", ".join([f"{x:.2f}{currency}" for x in forecast])

    return (
        f"Витрати на {category} {action}. "
        f"Середні: {avg:.2f}{currency}, останні: {last_value:.2f}{currency}. "
        f"Прогноз на наступні {len(forecast)} місяці: {forecast_text}. "
        f"{suggestion}."
    )


def calculate_trend_coefficient(values):
    """Обчислює коефіцієнт тренду за допомогою лінійної регресії."""
    x = np.arange(len(values))
    y = np.array(values)
    # Виконуємо лінійну регресію, де slope — це коефіцієнт тренду
    slope, _ = np.polyfit(x, y, 1)
    return slope