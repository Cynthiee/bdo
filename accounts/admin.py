# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, CustomerProfile

class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False
    verbose_name_plural = 'Customer Profile'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (CustomerProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'phone_number', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {'fields': ('user_type', 'phone_number', 'date_of_birth', 'address', 'profile_picture')}),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('username',)

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'user', 'id_document_type', 'id_document_number', 'occupation')
    search_fields = ('customer_id', 'user__username', 'id_document_number')
    list_filter = ('id_document_type',)

# Register the custom User admin
admin.site.register(User, CustomUserAdmin)