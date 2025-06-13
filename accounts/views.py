from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView, UpdateView, DetailView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm, CustomerProfileForm, CustomLoginForm
from .models import User, CustomerProfile
import uuid
from bdounibank . models import BankAccount
from transactions.models import Transaction

class SignUpView(CreateView):
    model = User
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('profile_setup')
    template_name = 'accounts/signup.html'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Set user type to customer
        self.object.user_type = 'customer'
        self.object.save()
        
        # Log the user in
        raw_password = form.cleaned_data.get('password1')
        user = authenticate(username=self.object.username, password=raw_password)
        login(self.request, user)
        
        return response

class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'accounts/login.html'
    
    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')
        if not remember_me:
            # Session expires when browser closes
            self.request.session.set_expiry(0)
        
        return super().form_valid(form)
    
    
@login_required
def profile_setup_view(request):
    if hasattr(request.user, 'customer_profile'):
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            # Generate a unique customer ID
            profile.customer_id = f"BDO-{uuid.uuid4().hex[:8].upper()}"
            profile.save()
            return redirect('dashboard')
    else:
        form = CustomerProfileForm()
    
    return render(request, 'accounts/profile_setup.html', {'form': form})

class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'user'
    
    def get_object(self):
        return self.request.user

class UpdateProfileView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'email', 'phone_number', 'date_of_birth', 'address']
    template_name = 'accounts/update_profile.html'
    success_url = reverse_lazy('profile')
    
    def get_object(self):
        return self.request.user
    
