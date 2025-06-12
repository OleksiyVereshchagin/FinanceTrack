from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect
from django.urls import path
from main import views

urlpatterns = [
    path('', views.account_list, name='home'),
    path('logout', LogoutView.as_view(next_page='login'), name='logout'),
    path('accounts/', views.account_list),
    path('accounts/create/', views.account_create, name='account_create'),
    path('accounts/<int:pk>/edit/', views.account_edit, name='account_edit'),
    path('accounts/<int:pk>/delete/', views.account_delete, name='account_delete'),
]