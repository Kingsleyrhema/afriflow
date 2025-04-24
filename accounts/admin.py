from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'full_name', 'business_type', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'business_type')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone_number', 'country', 'state_province', 'preferred_language', 'language', 'business_type', 'pin', 'voice_mode', 'enable_biometrics_login')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'full_name', 'phone_number', 'country', 'state_province', 'preferred_language', 'language', 'business_type', 'pin', 'voice_mode', 'enable_biometrics_login', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email', 'full_name')
    ordering = ('email',)

admin.site.register(CustomUser, CustomUserAdmin)
