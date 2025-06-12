from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from finance.models import Account
from .forms import AccountForm



# 1. Перегляд списку рахунків
@login_required
def account_list(request):
    accounts = Account.objects.filter(user=request.user)
    return render(request, 'main/account_list.html', {'accounts': accounts})

# 2. Створення нового рахунку
@login_required
def account_create(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user = request.user
            account.save()
            messages.success(request, 'Рахунок створено.')
            return redirect('home')
    else:
        form = AccountForm()
    return render(request, 'main/account_form.html', {'form': form})

# 3. Редагування рахунку
@login_required
def account_edit(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            messages.success(request, 'Рахунок оновлено.')
            return redirect('home')
    else:
        form = AccountForm(instance=account)
    return render(request, 'main/account_form.html', {'form': form})

# 4. Видалення рахунку
@login_required
def account_delete(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    if request.method == 'POST':
        account.delete()
        messages.success(request, 'Рахунок видалено.')
        return redirect('home')
    return render(request, 'main/account_confirm_delete.html', {'account': account})

