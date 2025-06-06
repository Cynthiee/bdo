from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('accounts/', views.account_list_view, name='account_list'),
    path('accounts/create/', views.create_account_view, name='create_account'),
    path('accounts/<str:account_number>/', views.account_detail_view, name='account_detail'),
]