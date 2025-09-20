import asyncio
import json
import random
import re
from random import choice, randint, random, uniform
import string
from django.utils.crypto import get_random_string

import aiohttp
from django.db.models import Q
from django.shortcuts import render
from django.views.generic import ListView, DetailView, View

from .models import Category, Item
from magaz.models import Magaz, Category as Magazcat
from brands.models import Magaz as Brand
from blog.models import Item as Blog

from .forms import CommentForm
from django.shortcuts import redirect

from django.core.cache import cache
from itertools import groupby
from django.conf import settings


def prepare_words_list(words_string):
    """
    Разбивает строку на список слов и перемешивает их.
    """
    if not words_string:
      return []
    words = words_string.split(', ')
    #random.shuffle(words)
    return words
    
async def fetch_market_data(catt_title):
    """
    Асинхронно получает данные из API Яндекс Маркета.
    """
    cache_key = get_random_string(length=32)
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    headers = {'Authorization': '0K5YIDGFhKpohFnX5IjGUYAhvs27iW'}
    url = f'https://api.content.market.yandex.ru/v3/affiliate/search?text={catt_title}&geo_id=213&clid=3150662&fields=MODEL_PRICE,MODEL_RATING,MODEL_DEFAULT_OFFER,MODEL_MEDIA,OFFER_PHOTO,OFFER_DELIVERY&count=30'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=4) as response:
                response.raise_for_status() # Проверим на ошибки HTTP
                market_text = await response.text()
                market = json.loads(market_text)
                totalItems = market['context']
                market_items = market['items']
                cache.set(cache_key, {'market': market_items, 'totalItems': totalItems}, 300) #Кешируем на 5 минут
                return {'market': market_items, 'totalItems': totalItems}
    except aiohttp.ClientError as e:
        return {"error": f'Ошибка запроса к API Яндекс Маркета: {e}'}
    except json.JSONDecodeError as e:
        return {"error": f'Ошибка декодирования JSON: {e}'}
    except Exception as e:
        return {"error": f'Неизвестная ошибка: {e}'}
        
class CategoryView(ListView):
    """Категория товаров"""
    model = Item
    paginate_by = 36
    template_name = "category.html"


    def get_queryset(self):
        category_slug = self.kwargs['slug']
        category = Category.objects.get(slug=category_slug)
        descendant_categories = category.get_descendants(include_self=True)
        queryset = Item.objects.filter(category__in=descendant_categories).order_by('?')
        return queryset
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs['slug']
        category = Category.objects.get(slug=category_slug)
        context['cats_all'] = Category.objects.all()
        context['cat_descr'] = category.description
        context['cat_title'] = category
        
        word = category.name.split(' ')[0]
        context['first_word'] = word
        context["main_lsi"] = prepare_words_list(category.main_lsi)
        



        # Хлебные крошки
        context['category_bread_crumbs'] = category.get_ancestors(include_self=False)
        context['category_children'] = category.get_children().filter(cat_city=False)
        
        context["most_read"] = Item.objects.filter(category__in=category.get_descendants(include_self=True)).order_by('-views')[:7]
        context["seo_text"] = Item.objects.filter(category__in=category.get_descendants(include_self=True)).order_by('?')[:9]
        
        context["category_descendants"] = category.get_siblings().filter(cat_city=False)
        
        context["next_category"] = Category.objects.filter(pk=category.id + 1).first()
        context["previous_category"] = Category.objects.filter(pk=category.id - 1).first()
        

        
        
        return context

class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.views += 1
        self.object.save()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object

        # Упрощаем получение категорий, используем select_related
        context['cats_all'] = Category.objects.all().order_by('?')
        
        #Получаем все товары разом
        prod = Item.objects.prefetch_related('category').order_by('name')
        
        context["neighbors1"] = prod.filter(pk=int(obj.id + 1))
        context["neighbors2"] = prod.filter(pk=int(obj.id - 1))
        
        context["meta_title"] = obj.name
        context["ratingValue"] = uniform(3.1, 4.9)
        context["reviewCount"] = randint(50, 1000)

        #Самые просматриваемые товары
        context["most_read"] = Item.objects.order_by('-views')[:24]
        
        # Готовим списки слов
        context["main_lsi"] = prepare_words_list(obj.category.main_lsi)[:30]
        context["keywords"] = prepare_words_list(obj.category.additional_lsi)
        context["additional_lsi"] = prepare_words_list(obj.category.additional_lsi)
        context["main_graf"] = prepare_words_list(obj.category.main_graf)
        context["search_suggestions"] = prepare_words_list(obj.category.search_suggestions)

        # Получаем связанные товары
        word = obj.name.split()[0]
        cat = obj.category_id
        context["related_items"] = Item.objects.filter(name__icontains=word, category=cat).order_by('?')[:24]
        context["seo_text"] = Item.objects.filter(category=cat).order_by('?')[:12]
        context["same_category"] = Item.objects.filter(category=cat).order_by('?')[:8]

        # Хлебные крошки
        context['category_bread_crumbs'] = obj.category.get_ancestors(include_self=True)
        
        
        # Подгружаем только те магазины, которые будут выводиться
        context['magaz'] = Magaz.objects.all().order_by('?')[:8]
        return context


class HomeView(ListView):
    model = Magaz
    paginate_by = 36
    template_name = "home.html"
    
    def get_magaz_list(self):
      """Получает список магазинов из settings, если он есть"""
      #magaz_ids = getattr(settings, 'HOME_PAGE_MAGAZ_IDS', [6218, 6322, 5131, 6339, 6327, 5077, 5575])
      return Magaz.objects.all()
    
    def get_categories(self):
      """Получает и обрабатывает категории для отображения на главной странице"""
      cats_all = Magazcat.objects.prefetch_related('parent').order_by('id') #Загружаем parent
      last_cats = cats_all.order_by('-id')
      home_cats = {parent: list(children) for parent, children in groupby(cats_all, key=lambda cat: cat.parent)}
      return {'cats_all': cats_all, 'last_cats': last_cats, 'home_cats_sorted': home_cats}
    
    
    def get_items(self):
      """Получает и обрабатывает данные по товарам"""
      prod = Item.objects.all() 
      brand = Brand.objects.all() 
      most_read = prod.order_by('-views')[:8]
      last_prod = prod.order_by('?').exclude(description='').filter(description__isnull=False)[:12]
      #last_prod = prod.order_by('?')[:12]
      last_brand = brand.order_by('?').exclude(description='').filter(description__isnull=False)[:24]
      sezon = prod.order_by('?')[:8]
      return {"most_read": most_read, "last_prod": last_prod, "last_brand": last_brand, "sezon": sezon}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем данные по категориям
        categories_data = self.get_categories()
        context.update(categories_data)
        
        #Получаем данные по товарам
        items_data = self.get_items()
        context.update(items_data)
        
      
        # Получаем список магазинов
        magazin = self.get_magaz_list().order_by('?')
        context['magaz'] = magazin[:24]
        context['posts'] = Blog.objects.all().order_by('?')[:24]
        
        return context

class AddComment(View):
    def post(self, request, pk):
        form = CommentForm(request.POST)
        item = Item.objects.get(id=pk)
        if form.is_valid():
            form = form.save(commit=False)
            form.item = item
            form.save()
        return redirect(item.get_absolute_url())