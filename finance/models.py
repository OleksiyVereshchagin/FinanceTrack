from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.db.models import F
from django.utils.functional import cached_property
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django import forms
from django.utils import timezone
from django.core.validators import MinValueValidator


class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='UAH')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name} ({self.currency})'


class Category(models.Model):
    TYPE_CHOICES = (
        ('income', 'Доходи'),
        ('expense', 'Витрати'),
    )
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=7, choices=TYPE_CHOICES)

    class Meta:
        unique_together = ('name', 'type')

    def __str__(self):
        return f"{self.name} ({self.type})"




class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Дохід'),
        ('expense', 'Витрата'),
        ('transfer', 'Переказ'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)

    account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.CASCADE, related_name='transactions')
    source_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL, related_name='outgoing_transfers')
    target_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL, related_name='incoming_transfers')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Зберігаємо старі значення для редагування
        self._original_type = self.type
        self._original_amount = self.amount
        self._original_account = self.account
        self._original_source_account = self.source_account
        self._original_target_account = self.target_account

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        if not is_new:
            # Скасування впливу старої транзакції
            self._revert_old_transaction()

        super().save(*args, **kwargs)

        # Застосування нової транзакції
        self._apply_transaction()

    def delete(self, *args, **kwargs):
        self._revert_old_transaction()
        super().delete(*args, **kwargs)

    def _revert_old_transaction(self):
        if self._original_type == 'income' and self._original_account:
            self._original_account.balance = F('balance') - self._original_amount
            self._original_account.save(update_fields=['balance'])

        elif self._original_type == 'expense' and self._original_account:
            self._original_account.balance = F('balance') + self._original_amount
            self._original_account.save(update_fields=['balance'])

        elif self._original_type == 'transfer':
            if self._original_source_account:
                self._original_source_account.balance = F('balance') + self._original_amount
                self._original_source_account.save(update_fields=['balance'])
            if self._original_target_account:
                self._original_target_account.balance = F('balance') - self._original_amount
                self._original_target_account.save(update_fields=['balance'])

    def _apply_transaction(self):
        if self.type == 'income' and self.account:
            self.account.balance = F('balance') + self.amount
            self.account.save(update_fields=['balance'])

        elif self.type == 'expense' and self.account:
            self.account.balance = F('balance') - self.amount
            self.account.save(update_fields=['balance'])

        elif self.type == 'transfer':
            if self.source_account:
                self.source_account.balance = F('balance') - self.amount
                self.source_account.save(update_fields=['balance'])
            if self.target_account:
                self.target_account.balance = F('balance') + self.amount
                self.target_account.save(update_fields=['balance'])



class Goal(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('completed', 'Виконана'),
        ('failed', 'Провалена'),
    ]

    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    title = models.CharField(max_length=100, verbose_name="Назва цілі")
    description = models.TextField(blank=True, verbose_name="Опис цілі")
    target_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Цільова сума"
    )
    current_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Поточна сума"
    )
    start_date = models.DateField(default=timezone.now, verbose_name="Дата початку")
    end_date = models.DateField(verbose_name="Дата завершення")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-end_date']
        verbose_name = "Ціль"
        verbose_name_plural = "Цілі"

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def progress(self):
        """Розраховує прогрес у відсотках"""
        if self.target_amount == 0:
            return 0
        return (self.current_amount / self.target_amount) * 100

    def update_status(self):
        """Оновлює статус цілі автоматично"""
        if self.current_amount >= self.target_amount:
            self.status = 'completed'
        elif timezone.now().date() > self.end_date:
            self.status = 'failed'
        else:
            self.status = 'active'
        self.save()

    def monthly_saving_needed(self):
        """Розраховує щомісячний внесок для досягнення цілі"""
        months_left = (self.end_date - timezone.now().date()).days / 30
        if months_left <= 0:
            return self.target_amount - self.current_amount
        return (self.target_amount - self.current_amount) / months_left


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['title', 'target_amount', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        today = timezone.now().date()
        self.fields['start_date'].initial = today
        self.fields['end_date'].initial = today + timezone.timedelta(days=30)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                self.add_error('end_date', "Дата завершення не може бути раніше дати початку")

            if end_date < timezone.now().date():
                self.add_error('end_date', "Дата завершення не може бути в минулому")

        return cleaned_data


#
# class Goal(models.Model):
#     GOAL_TYPES = [
#         ('saving', 'Накопичення'),
#         ('limit', 'Ліміт витрат'),
#         ('reduce', 'Зменшення витрат'),
#     ]
#
#     STATUS_CHOICES = [
#         ('in_progress', 'В процесі'),
#         ('completed', 'Досягнуто'),
#         ('expired', 'Не досягнуто вчасно'),
#     ]
#
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     type = models.CharField(max_length=10, choices=GOAL_TYPES)
#     title = models.CharField(max_length=100)
#     description = models.TextField(blank=True)
#
#     category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
#
#     target_amount = models.DecimalField(max_digits=12, decimal_places=2)
#     current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
#
#     start_date = models.DateField()
#     end_date = models.DateField()
#
#     status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='in_progress')
#
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f"{self.title} ({self.get_type_display()})"
#
#     def clean(self):
#         if self.type in ['limit', 'reduce'] and not self.category:
#             raise ValidationError("Для типів 'Ліміт' або 'Зменшення' потрібно обрати категорію.")
#         if self.type == 'saving' and self.category:
#             raise ValidationError("Для типу 'Накопичення' не потрібно вказувати категорію.")
#
#     def progress_percent(self):
#         if self.target_amount == 0:
#             return 0
#         progress = (self.current_amount / self.target_amount) * 100
#         return min(round(progress, 2), 100)


















# class Transaction(models.Model):
#     TRANSACTION_TYPES = (
#         ('income', 'Доходи'),
#         ('expense', 'Витрати'),
#         ('transfer', 'Переказ'),
#     )
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     type = models.CharField(max_length=8, choices=TRANSACTION_TYPES)
#     title = models.CharField(max_length=255)
#     amount = models.DecimalField(max_digits=12, decimal_places=2)
#     date = models.DateField(default=timezone.now)
#
#     # Для income/expense
#     account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
#     category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
#
#     # Для transfer
#     source_account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, related_name='outgoing_transfers')
#     target_account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, related_name='incoming_transfers')
#
#     def __str__(self):
#         return f"{self.title} - {self.amount} {self.type}"
#
