from django.contrib import admin
from .models import TelegramUser, ModelProfile, ModelPhoto, Order


class ModelPhotoInline(admin.TabularInline):
    model = ModelPhoto
    extra = 1


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'username', 'created_at')
    search_fields = ('telegram_id', 'username')
    list_filter = ('created_at',)


@admin.register(ModelProfile)
class ModelProfileAdmin(admin.ModelAdmin):
    inlines = [ModelPhotoInline]
    list_display = ('name', 'price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'model', 'status', 'created_at')
    list_filter = ('status',)
    actions = ['mark_as_paid']

    def mark_as_paid(self, request, queryset):
        queryset.update(status='paid')
        # Здесь можно добавить отправку уведомлений через бота
    mark_as_paid.short_description = "Подтвердить оплату"
