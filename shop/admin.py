# shop/admin.py
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.shortcuts import render
from django.contrib import messages
from django.utils.html import format_html
from .models import Category, Item
from .tasks import sync_category_products_task

from mptt.admin import MPTTModelAdmin, TreeRelatedFieldListFilter

from import_export.admin import ImportExportActionModelAdmin, ImportExportModelAdmin

# shop/admin.py
import logging
logger = logging.getLogger(__name__)

def sync_view(self, request, category_id):
    logger.info(f"✅ sync_view вызван для категории ID={category_id}")
    print(f"🔧 sync_view вызван: category_id={category_id}")

    try:
        category = Category.objects.get(pk=category_id)
        logger.info(f"✅ Категория найдена: {category.name}")
        print(f"✅ Категория: {category.name}")

        sync_category_products_task.delay(category.name)
        logger.info(f"🚀 Задача отправлена: sync_category_products_task('{category.name}')")
        print(f"🚀 Задача отправлена")

        messages.success(request, f'Синхронизация запущена для "{category.name}"')
    except Category.DoesNotExist:
        logger.error(f"❌ Категория с ID={category_id} не найдена")
        messages.error(request, 'Категория не найдена.')
    except Exception as e:
        logger.error(f"❌ Ошибка в sync_view: {e}", exc_info=True)
        messages.error(request, f'Ошибка: {e}')

    return HttpResponseRedirect(reverse('admin:shop_category_changelist'))


@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin, MPTTModelAdmin):
    list_display = ("name", "id", "product_count", "sync_button")
    list_filter = ("name","id")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    save_on_top = True
    mptt_level_indent = 30
    mptt_indent_field = "name"
    
    class Media:
        js = ('shop/admin_sync_button.js',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('sync/<int:category_id>/', self.admin_site.admin_view(self.sync_view), name='shop_category_sync_category'),
            # Изменили имя на 'sync_category' (без 'shop_')
        ]
        return custom_urls + urls

    def product_count(self, obj):
        return obj.products.count()

    product_count.short_description = "Товаров"

    def sync_button(self, obj):
        # Используем правильное полное имя URL
        url = reverse('admin:shop_category_sync_category', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" target="_blank">Получить товары</a>',
            url
        )

    sync_button.short_description = "Действие"

    def sync_view(self, request, category_id):
        try:
            category = Category.objects.get(pk=category_id)
            sync_category_products_task.delay(category.name)
            messages.success(
                request,
                f'Синхронизация запущена для категории "{category.name}".'
            )
        except Category.DoesNotExist:
            messages.error(request, 'Категория не найдена.')
        return HttpResponseRedirect(reverse('admin:shop_category_changelist'))

@admin.register(Item)
class ItemAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ("name", "category", "offer_price", "external_id")
    list_filter = ("category", "created_at")
    search_fields = ("name", "offer_sku")
    readonly_fields = ("external_id", "created_at", "updated_at")
    save_on_top = True
   