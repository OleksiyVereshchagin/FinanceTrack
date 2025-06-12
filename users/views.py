from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

from users.forms import CustomUserCreationForm


@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()

    return render(request, 'users/login.html', {'form': form})

# @never_cache
# def register_view(request):
#     if request.user.is_authenticated:
#         return redirect('home')
#
#     if request.method == 'POST':
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             login(request, user)  # Автоматично залогінити користувача
#             return redirect('home')  # Перенаправлення на головну сторінку
#     else:
#         form = UserCreationForm()
#
#     return render(request, 'users/register.html', {'form': form})

@never_cache
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')
