from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Ім'я користувача",
        widget=forms.TextInput(attrs={'placeholder': "Введіть логін"})
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={'placeholder': "Введіть пароль"})
    )


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
