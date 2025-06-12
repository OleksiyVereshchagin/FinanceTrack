from datetime import date
from dateutil.relativedelta import relativedelta
from django.db.models.functions import TruncMonth
from django.db.models import Sum
from .models import Transaction

def get_expense_trends(user):
    today = date.today()
    first_day_of_this_month = today.replace(day=1)
    start_date = first_day_of_this_month - relativedelta(months=3)

    recent_expenses = Transaction.objects.filter(
        user=user,
        type='expense',
        date__gte=start_date,
        date__lt=first_day_of_this_month,
        category__isnull=False,
    ).exclude(category__name__iexact='Переказ')

    by_month_and_category = recent_expenses.annotate(
        month=TruncMonth('date')
    ).values('month', 'category__name').annotate(
        total=Sum('amount')
    ).order_by('month')

    return by_month_and_category
