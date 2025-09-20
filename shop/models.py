from django.db import models
from django.contrib.postgres.fields import JSONField
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey

#from django.utils.text import slugify
from pytils.translit import slugify

from django.utils.crypto import get_random_string


class Category(MPTTModel):
    """Категории"""
    name = models.CharField("Категория", max_length=300, db_index=True)
    menutitle = models.CharField(
        "Короткое название", max_length=300, default='', blank=True)
    padej = models.CharField(
        "Падеж", max_length=300, default='', blank=True)
    description = models.TextField("Описание", default='', blank=True)
    slug = models.SlugField(max_length=300, unique=True)

    metatitle = models.TextField("<title>", default='', blank=True)
    metadescription = models.TextField(
        "<description>", default='', blank=True)

    plitka_top = models.TextField(
        "Верхняя плитка тэгов", default='', blank=True)
    plitka_bottom = models.TextField(
        "Нижняя плитка тэгов", default='', blank=True)
    plitka_search = models.TextField(
        "Плитка тэгов под поиском", default='', blank=True)
        
    
    main_lsi = models.TextField(
        "Основные связанные слова", default='', blank=True)
        
    additional_lsi = models.TextField(
        "Бренды", default='', blank=True)
        
    main_graf = models.TextField(
        "Основной семантический граф", default='', blank=True)
        
    search_suggestions = models.TextField(
        "Полный список поисковых подсказок", default='', blank=True)
        
    

    parent = TreeForeignKey('self', on_delete=models.CASCADE, blank=True, db_index=True,
                            null=True, related_name='children', verbose_name='Родительская категория')
    

           
    cat_city = models.BooleanField(default=False)

    @property
    def items_count(self):
        # получаем список идентификторов всех низлежащих категорий, включая интересующую нас
        ids = self.get_descendants(include_self=True).values_list('id')
        # возвращаем количество товаров, имеющих родителем категорию с идентификатором входящим
        # в список полученный строкой выше
        return Item.objects.filter(category_id__in=ids).count()

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("shop:category", kwargs={
            'slug': self.slug
        })

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Item(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Категория"
    )
    external_id = models.BigIntegerField("HID в Я.Маркете", unique=True, default='1')
    name = models.CharField("Название", max_length=500, db_index=True)
    description = models.TextField('Описание', blank=True, null=True)  
    
    link = models.URLField("Ссылка", max_length=1000, default='')
    price_min = models.DecimalField("Мин. цена", max_digits=12, decimal_places=2, null=True, blank=True)
    price_max = models.DecimalField("Макс. цена", max_digits=12, decimal_places=2, null=True, blank=True)
    offer_price = models.DecimalField("Цена предложения", max_digits=12, decimal_places=2, null=True, blank=True)
    specifications = models.JSONField("Характеристики", blank=True, null=True)
    image_url = models.URLField("Изображение", max_length=1000, blank=True, null=True)
    images_all = models.JSONField("Все Изображения", blank=True, null=True)
    offer_sku = models.CharField("SKU", max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    
    slug = models.SlugField(max_length=500, unique=True, blank=True)
    views = models.IntegerField("Просмотры", default=0) 
    
    for_posts = models.BooleanField(default=False, verbose_name='Основа для статьи')
    

    class Meta:
        verbose_name = "Товар Я.Маркета"
        verbose_name_plural = "Товары Я.Маркета"
        indexes = [
            models.Index(fields=['category', 'external_id']),
            models.Index(fields=['offer_price']),
        ]

    def __str__(self):
        return self.name
        
    def get_absolute_url(self):
        return reverse("shop:product", kwargs={
            'slug': self.slug
        })
        
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)[:40]  # Обрезаем slug до 30 символов
            random_digits = get_random_string(length=7, allowed_chars='0123456789')
            self.slug = f"{base_slug}-{random_digits}"
        super().save(*args, **kwargs) 

class Comments(models.Model):
    """Отзывы"""
    email = models.EmailField()
    name = models.CharField("Имя", max_length=150)
    text = models.TextField("Сообщение", max_length=5000)
    parent = models.ForeignKey('self', verbose_name="Родитель", on_delete=models.SET_NULL, blank=True, null=True)
    item = models.ForeignKey(Item, verbose_name="Товар", on_delete=models.CASCADE)
    published = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.item}"
        


    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"  