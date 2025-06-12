from django import forms
from finance.models import Account
import pycountry

def get_currency_choices():
    return sorted([(c.alpha_3, f'{c.name} ({c.alpha_3})') for c in pycountry.currencies], key=lambda x: x[1])

class AccountForm(forms.ModelForm):
    currency = forms.ChoiceField(
        choices=get_currency_choices(),
        label="Валюта",
        widget=forms.Select(attrs={'class': 'form-select-field'})
    )

    class Meta:
        model = Account
        fields = ['name', 'balance', 'currency']
        labels = {
            'name': 'Назва рахунку',
            'balance': 'Початковий баланс',
            'currency': 'Валюта',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input-field'}),
            'balance': forms.NumberInput(attrs={'class': 'form-input-field'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Вимикаємо автоматичну обов’язковість HTML-полів
        for field in self.fields.values():
            field.required = False

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        currency = cleaned_data.get('currency')

        if not name:
            self.add_error('name', "Введіть назву рахунку")
        if not currency:
            self.add_error('currency', "Оберіть валюту рахунку")

        try:
            balance = cleaned_data.get('balance')
            if balance is not None and balance < 0:
                self.add_error('balance', "Початковий баланс не може бути від’ємним")
        except Exception as e:
            raise forms.ValidationError(f"Помилка при перевірці балансу: {str(e)}")

        return cleaned_data
