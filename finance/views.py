import random
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView

from finance.forms import ExpenseAnalysisForm
from finance.models import Category, Transaction

from .advice_texts import advice_variants
from .forms import TransactionForm
from .models import Account, Goal
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from django.utils import timezone
from decimal import Decimal
from django.db.models import Min, Max
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import redirect


def transaction_list(request):
    user = request.user

    user_accounts = Account.objects.filter(user=user)
    categories = Category.objects.all()

    transactions = Transaction.objects.filter(user=user).select_related(
        'account', 'source_account', 'target_account', 'category'
    )

    account_id = request.GET.get('account')
    category_id = request.GET.get('category')

    if account_id:
        transactions = transactions.filter(
            account_id=account_id
        ) | transactions.filter(
            source_account_id=account_id
        ) | transactions.filter(
            target_account_id=account_id
        )

    if category_id:
        transactions = transactions.filter(category_id=category_id)

    sort_field = request.GET.get('sort')
    direction = request.GET.get('direction', 'asc')

    allowed_fields = {
        'date': 'date',
        'amount': 'amount',
        'type': 'type',
        'category__name': 'category__name',
        'account': 'account__name',
    }

    if sort_field in allowed_fields:
        sort_expr = allowed_fields[sort_field]
        if direction == 'desc':
            sort_expr = f'-{sort_expr}'
        transactions = transactions.order_by(sort_expr)

    context = {
        'transactions': transactions,
        'user_accounts': user_accounts,
        'categories': categories,
        'current_sort': sort_field or '',
        'current_direction': direction,
        'sort_fields': [
            ('amount', 'Сума'),
            ('type', 'Тип'),
            ('category__name', 'Категорія'),
            ('date', 'Дата'),
            ('account', 'Рахунок'),
        ],
    }

    return render(request, 'finance/transaction_list.html', context)

@login_required
def transaction_create(request):
    user_accounts = Account.objects.filter(user=request.user, is_active=True)
    categories = Category.objects.all()  # Або filter(user=request.user) для персональних категорій

    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('transaction')  # Або інша сторінка
    else:
        form = TransactionForm(user=request.user)

    return render(request, 'finance/transaction_form.html', {
        'form': form,
        'user_accounts': user_accounts,
        'categories': categories,
        'title': 'Додати нову транзакцію',
    })


@login_required
def transaction_edit(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('transaction')  # transaction_list
    else:
        form = TransactionForm(instance=transaction, user=request.user)

    user_accounts = Account.objects.filter(user=request.user, is_active=True)
    categories = Category.objects.all()

    return render(request, 'finance/transaction_form.html', {
        'form': form,
        'user_accounts': user_accounts,
        'categories': categories,
        'editing': True,
        'title': 'Редагувати транзакцію',
    })


@login_required
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        return redirect('transaction')  # transaction_list

    return render(request, 'finance/transaction_delete.html', {
        'transaction': transaction
    })


@login_required
def transaction_import(request):
    return render(request, 'finance/transaction_import.html')


@login_required
def get_categories_by_type(request):
    type_param = request.GET.get('type')
    if type_param in ['income', 'expense']:
        categories = Category.objects.filter(type=type_param).values('id', 'name')
        return JsonResponse(list(categories), safe=False)
    return JsonResponse([], safe=False)

class ExpenseAnalysisView(TemplateView):
    template_name = 'finance/expense_analysis.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        form = ExpenseAnalysisForm(user, self.request.GET or None)
        context['form'] = form

        if form.is_valid():
            account = form.cleaned_data['account']
            period = form.cleaned_data['period']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date'] or timezone.now().date()

            if period != 'custom':
                delta_days = {
                    'week': 7,
                    'month': 30,
                    '3months': 90,
                    '6months': 180,
                    'year': 365,
                }.get(period)
                if delta_days:
                    start_date = end_date - timedelta(days=delta_days)

            filter_params = {
                'user': user,
                'account': account,
                'date__gte': start_date,
                'date__lte': end_date,
            }

            expenses = Transaction.objects.filter(**filter_params, type='expense').select_related('category')
            incomes = Transaction.objects.filter(**filter_params, type='income')
            all_transactions = Transaction.objects.filter(**filter_params)

            context['transaction_count'] = all_transactions.count()

            # Умова 1: менше 7 транзакцій — не показуємо статистику взагалі
            if all_transactions.count() < 7:
                context['not_enough_data'] = True
                context['advice'] = []
                return context  # Вихід — більше нічого не обчислюємо

            context['not_enough_data'] = False

            # Умова 2: короткий період — не показуємо частину порад
            analysis_days = (end_date - start_date).days
            context['short_period'] = analysis_days < 7

            context['no_expenses'] = not expenses.exists()

            if expenses.exists():
                context['by_category'] = expenses.values('category__name').annotate(
                    total=Sum('amount')
                ).order_by('-total')

                context['by_day'] = expenses.values('date').annotate(
                    total=Sum('amount')
                ).order_by('date')

                context['avg_by_category'] = expenses.values('category__name').annotate(
                    avg=Avg('amount')
                ).order_by('-avg')

                context['count_by_category'] = expenses.values('category__name').annotate(
                    count=Count('id')
                ).order_by('-count')

                context['total_expenses'] = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
                context['avg_per_day'] = round(expenses.aggregate(avg=Avg('amount'))['avg'] or 0, 2)

                context['top_category'] = expenses.values('category__name').annotate(
                    total=Sum('amount')
                ).order_by('-total').first()

                context['expenses_by_day'] = list(
                    expenses.values('date').annotate(total=Sum('amount')).order_by('date')
                )

            total_income = incomes.aggregate(Sum('amount'))['amount__sum'] or 0
            context['total_income'] = total_income

            total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
            context['total_expenses'] = total_expenses

            context['balance'] = total_income - total_expenses

            context['incomes_by_day'] = list(
                incomes.values('date').annotate(total=Sum('amount')).order_by('date')
            )

            advice = []

            if not context['short_period']:
                # 1. Категорія > 40% усіх витрат — лише якщо є достатньо транзакцій
                if expenses.count() >= 7:
                    by_cat = expenses.values('category__name').annotate(sum=Sum('amount'))
                    for cat in by_cat:
                        if cat['sum'] > total_expenses * Decimal('0.4'):
                            advice.append(
                                random.choice(advice_variants['high_category_spending']).format(
                                    cat=cat['category__name'])
                            )

                # 2. Доходи менші за витрати
                if total_income < total_expenses:
                    advice.append(random.choice(advice_variants['expenses_exceed_income']))

                # 4. Відсутність заощаджень
                if not expenses.filter(category__name='Заощадження / Відкладено').exists():
                    advice.append(random.choice(advice_variants['no_savings_activity']))

            # 5. Сплески витрат — лише якщо є принаймні 4 дні з витратами
            if context.get('expenses_by_day'):
                day_values = [entry['total'] for entry in context['expenses_by_day']]
                if len(day_values) >= 4:
                    avg_day = sum(day_values) / len(day_values)
                    if any(v > avg_day * 2 for v in day_values):
                        advice.append(random.choice(advice_variants['spikes_in_expenses']))

            context['advice'] = advice
            # --- Кінець блоку порад ---

            # Оновлений блок з середнім по категоріях (тільки з кількістю >1)
            context['avg_by_category'] = expenses.values('category__name').annotate(
                avg=Avg('amount'),
                count=Count('id')
            ).filter(count__gt=1).order_by('-avg')

        return context

@login_required
def add_goal_view(request):
    if request.method == 'POST':
        form = GoalForm(request.POST, user=request.user)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            return redirect('recommendations')
    else:
        form = GoalForm(user=request.user)

    return render(request, 'finance/add_goal.html', {'form': form})


@login_required
def recommendations_view(request):
    trend_analysis = analyze_trends(request.user)
    goals = Goal.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'finance/recommendations.html', {
        'trend_data': trend_analysis,
        'goals': goals,
    })



def expense_analysis(request):
    if not request.user.is_authenticated:
        return redirect('login')

    trends = analyze_trends(request.user)

    # Конвертуємо дані в безпечний JSON
    for trend in trends:
        trend['months_json'] = json.dumps(trend['months'], cls=DjangoJSONEncoder)
        trend['values_json'] = json.dumps(trend['values'], cls=DjangoJSONEncoder)

    return render(request, 'finance/recommendations.html', {
        'trend_data': trends
    })


def analyze_trends(user, min_months=3, min_transactions=3, min_amount=500, trend_threshold=20, window_size=3):
    today = timezone.now().date()
    user_main_currency = 'UAH'  # Основна валюта користувача

    # Визначаємо діапазон дат
    first_transaction = Transaction.objects.filter(
        user=user,
        type='expense',
        date__lt=today
    ).exclude(type='transfer').aggregate(Min('date'))['date__min']

    last_transaction = Transaction.objects.filter(
        user=user,
        type='expense',
        date__lt=today
    ).exclude(type='transfer').aggregate(Max('date'))['date__max']

    if not first_transaction or not last_transaction:
        return []

    # Визначаємо кількість місяців
    months_diff = (last_transaction.year - first_transaction.year) * 12 + \
                  (last_transaction.month - first_transaction.month)
    months_back = max(min_months, months_diff + 1)

    # Генеруємо список місяців
    months = [(today - relativedelta(months=i)).replace(day=1)
              for i in reversed(range(months_back))
              if (today - relativedelta(months=i)).replace(day=1) <= last_transaction]

    if len(months) < min_months:
        return []

    start_date = months[0]
    end_date = (months[-1] + relativedelta(months=1)).replace(day=1)

    # Отримуємо транзакції
    transactions = Transaction.objects.filter(
        user=user,
        type='expense',
        date__gte=start_date,
        date__lt=end_date,
    ).exclude(type='transfer').select_related('category', 'account')

    # Групуємо по категоріям та валютам
    category_data = defaultdict(lambda: defaultdict(lambda: {
        'values': [Decimal('0.00') for _ in range(len(months))],
        'count': 0,
        'currency': None
    }))

    for tx in transactions:
        category_name = tx.category.name if tx.category else "Без категорії"
        currency = tx.account.currency if tx.account and tx.account.currency else user_main_currency

        # Якщо валюта не UAH - додаємо її в назву категорії
        display_category = f"{category_name} ({currency})" if currency != user_main_currency else category_name

        for i, m in enumerate(months):
            if tx.date.year == m.year and tx.date.month == m.month:
                category_data[display_category][currency]['values'][i] += tx.amount
                category_data[display_category][currency]['count'] += 1
                category_data[display_category][currency]['currency'] = currency
                break

    # Аналіз трендів
    results = []
    for category, currencies in category_data.items():
        for currency, data in currencies.items():
            values = data['values']
            total = sum(values)

            # Фільтрація незначних категорій
            if (data['count'] < min_transactions or
                    total < min_amount or
                    sum(1 for v in values if v > 0) < 2):
                continue

            # Обробка даних
            non_zero_values = [float(v) for v in values if v > 0]
            if not non_zero_values:
                continue

            # Ковзне середнє
            moving_avg = []
            for i in range(len(non_zero_values) - window_size + 1):
                window = non_zero_values[i:i + window_size]
                moving_avg.append(sum(window) / len(window))

            # Вагове середнє для прогнозу
            weights = list(range(1, len(non_zero_values) + 1))
            weighted_sum = sum(v * w for v, w in zip(non_zero_values, weights))
            weighted_avg = weighted_sum / sum(weights)

            # Визначення тренду
            trend = "stable"
            change_percent = 0
            if len(moving_avg) > 1:
                first = moving_avg[0]
                last = moving_avg[-1]
                change_percent = ((last - first) / first) * 100 if first != 0 else 0

                if abs(change_percent) > trend_threshold:
                    trend = "increase" if change_percent > 0 else "decrease"

            # Прогноз
            last_value = non_zero_values[-1]
            forecast = last_value + (weighted_avg - last_value) * (1 + abs(change_percent) / 100)
            forecast = max(forecast, 0.0)

            # Форматування результатів
            results.append({
                'category': category,
                'months': [m.strftime('%b %Y') for m in months],
                'values': [float(v) for v in values],
                'trend': trend,
                'change_percent': round(change_percent, 1),
                'forecast': round(forecast, 2),
                'currency': currency,
                'insight': generate_insight(category.split(' (')[0], trend, change_percent, forecast, currency, values)
            })

    # Сортування за зміною (за абсолютним значенням)
    return sorted(results, key=lambda x: abs(x['change_percent']), reverse=True)


def generate_insight(category, trend, percent, forecast, currency, values):
    """Генерує персоналізовані текстові рекомендації"""
    # Convert all Decimal values to float for calculations
    last_value = float(values[-1]) if values else 0.0
    prev_value = float(values[-2]) if len(values) > 1 else last_value
    values_float = [float(v) for v in values] if values else [0.0]
    max_value = max(values_float) if values_float else 0.0
    forecast = float(forecast)
    percent = float(percent)

    # Визначаємо тип категорії для точніших рекомендацій
    category_types = {
        'Їжа': 'essential',
        'Транспорт': 'essential',
        'Медицина': 'health',
        'Комунальні послуги': 'fixed',
        'Одяг': 'variable',
        'Розваги': 'discretionary',
        'Подарунки': 'occasional',
        'Побутові товари': 'essential',
        'Освіта': 'investment',
        'Абонементи/підписки': 'subscription',
        'Домашні улюбленці': 'essential',
        'Інтернет / TV': 'fixed',
        'Подорожі': 'discretionary',
        'Податки': 'fixed',
        'Інше': 'other',
        'Заощадження': 'savings',
        'Благодійність / Донати': 'charity',
        'Краса / Догляд за собою': 'personal',
        'Діти / Родина': 'family',
        'Авто / Паливо / Обслуговування': 'transport',
        'Хобі / Творчість': 'hobby',
        'Оренда житла': 'fixed'
    }

    category_type = category_types.get(category.split('/')[0].strip(), 'other')

    if 0 in values_float[-2:]:
        if category_type in ['discretionary', 'hobby', 'personal']:
            return f"{category} → Нерегулярні витрати. Рекомендуємо встановити місячний ліміт у розмірі {max_value*0.7:.0f}-{max_value:.0f} {currency}."
        elif category_type in ['essential', 'health', 'transport']:
            return f"{category} → Пропущені витрати. Запланована сума на наступний місяць: {forecast:.0f} {currency}."
        else:
            avg = sum(values_float)/len(values_float) if values_float else 0
            return f"{category} → Нестабільний графік витрат. Середня сума: {avg:.0f} {currency}."

    if trend == 'increase':
        if category_type in ['subscription', 'fixed']:
            return f"{category} (+{abs(percent):.0f}%) → Зростання фіксованих витрат. Рекомендація: переглянути умови договорів."
        elif category_type in ['discretionary', 'hobby']:
            return f"{category} ({prev_value:.0f} → {last_value:.0f} {currency}) → Рекомендований ліміт: не більше {last_value*0.8:.0f} {currency}."
        elif category_type == 'essential':
            return f"{category} (+{abs(percent):.0f}%) → Оптимальний бюджет: {last_value*0.9:.0f}-{last_value:.0f} {currency}."
        else:
            avg = sum(values_float)/len(values_float) if values_float else 0
            return f"{category} → Зростання на {abs(percent):.0f}%. Середнє значення: {avg:.0f} {currency}."

    elif trend == 'decrease':
        if category_type in ['discretionary', 'hobby']:
            return f"{category} (-{abs(percent):.0f}%) → Вдала економія. Можна заощадити ще {last_value*0.1:.0f}-{last_value*0.2:.0f} {currency}."
        elif category_type == 'essential':
            return f"{category} → Економія {abs(percent):.0f}%. Оптимальний діапазон: {last_value:.0f}-{last_value*1.1:.0f} {currency}."
        else:
            saved = prev_value - last_value
            return f"{category} → Позитивна динаміка (-{abs(percent):.0f}%). Заощаджено: {saved:.0f} {currency}."

    else:  # stable
        if category_type in ['fixed', 'subscription']:
            return f"{category} → Стабільні витрати ({last_value:.0f} {currency}). Гарний показник."
        elif category_type in ['discretionary', 'hobby']:
            avg = sum(values_float)/len(values_float) if values_float else 0
            return f"{category} → Витрати під контролем. Середнє значення: {avg:.0f} {currency}."
        else:
            return f"{category} → Стабільна динаміка. Рекомендований бюджет: {last_value*0.9:.0f}-{last_value*1.1:.0f} {currency}."