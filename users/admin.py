from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import FavoriteInstrument

@admin.register(FavoriteInstrument)
class FavoriteInstrumentAdmin(admin.ModelAdmin):
    list_display = ['user', 'instrument']
    search_fields = ['user__username', 'instrument__code']


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_active', 'is_staff', 'date_joined')
    
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups')

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)