from django.contrib import admin
import models

admin.site.register(models.CustomUser)
admin.site.register(models.CustomUserManager)  # Register the CustomUser model with the admin site
# Register your models here.
