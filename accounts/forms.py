from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, CustomerProfile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )
    phone_number = forms.CharField(required=True)
    address = forms.CharField(widget=forms.Textarea, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 
                 'date_of_birth', 'phone_number', 'address', 
                 'password1', 'password2']

class CustomerProfileForm(forms.ModelForm):
    id_document_type = forms.ChoiceField(choices=[
        ('passport', 'Passport'),
        ('drivers_license', "Driver's License"),
        ('national_id', 'National ID'),
        ('other', 'Other')
    ])
    
    class Meta:
        model = CustomerProfile
        fields = ['id_document_type', 'id_document_number', 'occupation']

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'autofocus': True}))
    remember_me = forms.BooleanField(required=False, initial=False)