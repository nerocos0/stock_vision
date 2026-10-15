from django.contrib import admin

from .models import FavoriteInstrument

@admin.register(FavoriteInstrument)
class FavoriteInstrumentAdmin(admin.ModelAdmin):
    list_display = ['user', 'instrument', 'added_at']
    search_fields = ['user__username', 'instrument__code']
    list_filter = ['added_at']