from django.urls import path
from . import views

urlpatterns = [
    path('history/', views.transaction_history_view, name='transaction_history'),
    path('deposit/', views.deposit_view, name='deposit'),
    path('withdraw/', views.withdrawal_view, name='withdraw'),
    path('transfer/', views.transfer_view, name='transfer'),
]