from django.urls import path
from . import views

urlpatterns = [
    path('', views.loan_list_view, name='loan_list'),
    path('apply/', views.loan_application_view, name='loan_application'),
    path('payment/', views.loan_payment_view, name='loan_payment'),
    path('<uuid:loan_id>/', views.loan_detail_view, name='loan_detail'),
]