from django.contrib.postgres.indexes import BrinIndex
from django.db import models
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey

from datetime import datetime



class Category(MPTTModel):
    """Категории"""
    title = models.CharField("Категория", max_length=300, db_index=True)
    menutitle = models.CharField("Короткое название", max_length=300, default='', blank=True)
    description = models.TextField("Описание", default='', blank=True)
    slug = models.SlugField(max_length=300, unique=True)

    metatitle = models.TextField("<title>", default='', blank=True)
    metadescription = models.TextField(
        "<meta name='description'>", default='', blank=True)

    plitka_top = models.TextField("Верхняя плитка тэгов", default='', blank=True)
    plitka_bottom = models.TextField("Нижняя плитка тэгов", default='', blank=True)
    plitka_search = models.TextField("Плитка тэгов под поиском", default='', blank=True)

    parent = TreeForeignKey('self', on_delete=models.CASCADE, blank=True, db_index=True,
                            null=True, related_name='children', verbose_name='Родительская категория')
    @property
    def items_count(self):
        # получаем список идентификторов всех низлежащих категорий, включая интересующую нас
        ids = self.get_descendants(include_self=True).values_list('id')
        # возвращаем количество товаров, имеющих родителем категорию с идентификатором входящим
        # в список полученный строкой выше
        return Item.objects.filter(category_id__in=ids).count()

    class MPTTMeta:
        order_insertion_by = ['title']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:posts", kwargs={
            'slug': self.slug
        })

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

class Author(models.Model):
    """Model representing an author."""
    author_name = models.CharField(max_length=500)
    author_image = models.ImageField(upload_to ='media/authors/', default='', blank=True)
    author_posts = models.PositiveIntegerField(default=0,)
    slug = models.SlugField(max_length=300, unique=True, default='')
    description = models.TextField("Описание", default='', blank=True)

    class Meta:
        ordering = ['author_name', 'author_posts']

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse("blog:author", kwargs={'slug': self.slug})
       
    def __str__(self):
        return self.author_name
        
class AuthorCategory(MPTTModel):
    """Категории"""
    title = models.CharField("Категория", max_length=300, db_index=True)
    menutitle = models.CharField("Короткое название", max_length=300, default='', blank=True)
    description = models.TextField("Описание", default='', blank=True)
    slug = models.SlugField(max_length=300, unique=True)

    metatitle = models.TextField("<title>", default='', blank=True)
    metadescription = models.TextField(
        "<meta name='description'>", default='', blank=True)

    plitka_top = models.TextField("Верхняя плитка тэгов", default='', blank=True)
    plitka_bottom = models.TextField("Нижняя плитка тэгов", default='', blank=True)
    plitka_search = models.TextField("Плитка тэгов под поиском", default='', blank=True)

    parent = TreeForeignKey('self', on_delete=models.CASCADE, blank=True, db_index=True,
                            null=True, related_name='children', verbose_name='Родительская категория')
    @property
    def items_count(self):
        # получаем список идентификторов всех низлежащих категорий, включая интересующую нас
        ids = self.get_descendants(include_self=True).values_list('id')
        # возвращаем количество товаров, имеющих родителем категорию с идентификатором входящим
        # в список полученный строкой выше
        return Item.objects.filter(category_id__in=ids).count()

    class MPTTMeta:
        order_insertion_by = ['title']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:authors", kwargs={
            'slug': self.slug
        })

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        

class Item(models.Model):
    is_published = models.BooleanField(default=False, verbose_name='Опубликован')
    title = models.CharField("Название", max_length=500, db_index=True)
    
    category = models.ForeignKey('Category', models.CASCADE, verbose_name='категория', null=True)  
    slug = models.SlugField(max_length=500, unique=True)
    
    metatitle  = models.TextField("<title>", default='', null=True, blank=True)
    metadescription  = models.TextField("<meta name='description'>", default='', null=True, blank=True)    
    
    description = models.TextField('Описание', default='', null=True, blank=True)
    shortdescription = models.TextField("Краткое описание", default='', null=True, blank=True)
    image = models.ImageField(upload_to ='media/uploads/')

    plitka_top = models.TextField("Верхняя плитка тэгов", default='', blank=True)
   
    
    
    
    publish_date = models.DateField(auto_now_add=True)
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null = True)
    views = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:post", kwargs={
            'slug': self.slug
        })
    
    

    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"
       
