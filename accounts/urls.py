from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='landing_page'), name='logout'), 
    path('profile-setup/', views.profile_setup_view, name='profile_setup'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update/', views.UpdateProfileView.as_view(), name='update_profile'),
]
