# finance/forms.py
from django import forms
from .models import Transaction, Account, Category
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.exceptions import ValidationError
from django import forms
from .models import Category

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['type', 'title', 'amount', 'date', 'account', 'category', 'source_account', 'target_account']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        self.fields['account'].queryset = Account.objects.filter(user=user)
        self.fields['source_account'].queryset = Account.objects.filter(user=user)
        self.fields['target_account'].queryset = Account.objects.filter(user=user)
        self.fields['category'].queryset = Category.objects.all()

        # Вимикаємо автоматичну обов’язковість HTML-полів
        for field in self.fields.values():
            field.required = False

    def clean(self):
        cleaned_data = super().clean()

        transaction_type = cleaned_data.get('type')
        title = cleaned_data.get('title')
        amount = cleaned_data.get('amount')
        date = cleaned_data.get('date')
        account = cleaned_data.get('account')
        category = cleaned_data.get('category')
        source = cleaned_data.get('source_account')
        target = cleaned_data.get('target_account')

        # Загальні перевірки
        if not title:
            self.add_error('title', "Введіть назву операції")
        if not amount:
            self.add_error('amount', "Вкажіть суму операції")
        if not date:
            self.add_error('date', "Вкажіть дату")
        elif date > timezone.now().date():
            self.add_error('date', "Дата не може бути в майбутньому")

        # Перевірки по типу
        if transaction_type in ['income', 'expense']:
            if not account:
                self.add_error('account', "Для цього типу транзакції потрібно вибрати рахунок")
            if not category:
                self.add_error('category', "Оберіть категорію")
            cleaned_data['source_account'] = None
            cleaned_data['target_account'] = None

        elif transaction_type == 'transfer':
            if not source:
                self.add_error('source_account', "Оберіть рахунок відправника")
            if not target:
                self.add_error('target_account', "Оберіть рахунок одержувача")

            if source and target:
                if source == target:
                    raise forms.ValidationError("Не можна переказувати на той самий рахунок")
                if source.currency != target.currency:
                    raise forms.ValidationError("Неможливо здійснити переказ між рахунками з різною валютою")

            cleaned_data['account'] = None
            cleaned_data['category'] = None

        return cleaned_data




#
# class TransactionForm(forms.ModelForm):
#     class Meta:
#         model = Transaction
#         fields = ['type', 'title', 'amount', 'date', 'account', 'category', 'source_account', 'target_account']
#         widgets = {
#             'date': forms.DateInput(attrs={'type': 'date'}),
#         }
#
#     def __init__(self, *args, user=None, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.user = user
#
#         # Обмежуємо вибір рахунків для користувача
#         self.fields['account'].queryset = Account.objects.filter(user=user)
#         self.fields['source_account'].queryset = Account.objects.filter(user=user)
#         self.fields['target_account'].queryset = Account.objects.filter(user=user)
#
#         # Обмежуємо вибір категорій
#         self.fields['category'].queryset = Category.objects.all()
#
#         # Встановлюємо всі поля за замовчуванням як обов’язкові
#         for field_name in self.fields:
#             self.fields[field_name].required = False
#         # Але потім зробимо деякі поля необов’язковими залежно від типу — це в clean()
#
#     def clean(self):
#         cleaned_data = super().clean()
#         transaction_type = cleaned_data.get('type')
#         date = cleaned_data.get('date')
#
#         # Перевірка дати не в майбутньому
#         if date and date > timezone.now().date():
#             self.add_error('date', "Дата не може бути в майбутньому")
#
#         # Якщо є помилки після перевірки дати — припиняємо валідацію далі,
#         # щоб не додавати зайвих помилок
#         if self.errors:
#             return cleaned_data
#
#         # Далі перевіряємо обов’язкові поля залежно від типу
#         if transaction_type in ['income', 'expense']:
#             if not cleaned_data.get('account'):
#                 self.add_error('account', "Для цього типу транзакції потрібно вибрати рахунок")
#             if transaction_type == 'expense' and not cleaned_data.get('category'):
#                 self.add_error('category', "Для витрат потрібно вибрати категорію")
#             if not cleaned_data.get('title'):
#                 self.add_error('title', "Вкажіть назву транзакції")
#             if not cleaned_data.get('amount'):
#                 self.add_error('amount', "Вкажіть суму")
#             cleaned_data['source_account'] = None
#             cleaned_data['target_account'] = None
#
#         elif transaction_type == 'transfer':
#             if not cleaned_data.get('source_account'):
#                 self.add_error('source_account', "Виберіть рахунок відправника")
#             if not cleaned_data.get('target_account'):
#                 self.add_error('target_account', "Виберіть рахунок отримувача")
#             if cleaned_data.get('source_account') and cleaned_data.get('target_account'):
#                 if cleaned_data['source_account'] == cleaned_data['target_account']:
#                     self.add_error('target_account', "Не можна переказувати на той самий рахунок")
#                 if cleaned_data['source_account'].currency != cleaned_data['target_account'].currency:
#                     self.add_error('target_account', "Рахунки мають бути в одній валюті")
#             if not cleaned_data.get('title'):
#                 self.add_error('title', "Вкажіть назву транзакції")
#             if not cleaned_data.get('amount'):
#                 self.add_error('amount', "Вкажіть суму")
#             cleaned_data['account'] = None
#             cleaned_data['category'] = None
#
#         else:
#             raise forms.ValidationError("Виберіть коректний тип транзакції")
#
#         return cleaned_data





# class TransactionForm(forms.ModelForm):
#     class Meta:
#         model = Transaction
#         fields = ['type', 'title', 'amount', 'date', 'account', 'category', 'source_account', 'target_account']
#         widgets = {
#             'date': forms.DateInput(attrs={'type': 'date'}),
#         }
#
#     def __init__(self, *args, user=None, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.user = user
#
#         # Обмежуємо вибір рахунків тільки для поточного користувача
#         self.fields['account'].queryset = Account.objects.filter(user=user)
#         self.fields['source_account'].queryset = Account.objects.filter(user=user)
#         self.fields['target_account'].queryset = Account.objects.filter(user=user)
#
#         # Обмежуємо вибір категорій
#         self.fields['category'].queryset = Category.objects.all()
#
#     def clean(self):
#         cleaned_data = super().clean()
#         transaction_type = cleaned_data.get('type')
#         date = cleaned_data.get('date')
#
#         if date and date > timezone.now().date():
#             self.add_error('date', "Дата не може бути в майбутньому")
#
#         # Далі твоя логіка:
#         if transaction_type in ['income', 'expense']:
#             if not cleaned_data.get('account'):
#                 self.add_error('account', "Для цього типу транзакції потрібно вибрати рахунок")
#             cleaned_data['source_account'] = None
#             cleaned_data['target_account'] = None
#
#         elif transaction_type == 'transfer':
#             source = cleaned_data.get('source_account')
#             target = cleaned_data.get('target_account')
#
#             if not source or not target:
#                 raise forms.ValidationError("Для переказу потрібно вибрати обидва рахунки")
#
#             if source == target:
#                 raise forms.ValidationError("Не можна переказувати на той самий рахунок")
#
#             if source.currency != target.currency:
#                 raise forms.ValidationError("Неможливо здійснити переказ між рахунками з різною валютою")
#
#             cleaned_data['account'] = None
#             cleaned_data['category'] = None
#
#         return cleaned_data

class ExpenseAnalysisForm(forms.Form):
    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        empty_label=None,
        label="Рахунок",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required = True,
    )

    period = forms.ChoiceField(
        choices=[
            ('week', 'Тиждень'),
            ('month', 'Місяць'),
            ('3months', 'Квартал'),
            ('6months', 'Пів року'),
            ('year', 'Рік'),
            ('custom', 'Інший період'),
        ],
        initial='month',
        label="Період",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    start_date = forms.DateField(
        label="Початок",
        required=False,
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'},
            format='%Y-%m-%d')
    )

    end_date = forms.DateField(
        label="Кінець",
        required=False,
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'},
            format='%Y-%m-%d')
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = Account.objects.filter(user=user)

