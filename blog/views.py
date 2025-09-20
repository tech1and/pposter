import asyncio
import json
from random import random
from random import randint
from random import choice
from django.utils.text import slugify
import aiohttp
from django.views.generic import ListView, DetailView, View
from django.shortcuts import redirect
from blog.models import Item, Category, Author

from shop.models import Item as Prod


from django.db.models import Q
import re
from lxml import html
from collections import namedtuple
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
load_dotenv()
from django.db.models import F
from django.conf import settings
from django.core.cache import cache
from django.utils.functional import cached_property
from django.utils.crypto import get_random_string

YANDEX_API_KEY = str(os.getenv('YANDEX_API_KEY'))

def prepare_list(list_string):
    """Разделяет строку на список и перемешивает его."""
    if not list_string:
      return []
    items = list_string.split(',')
    random.shuffle(items)
    return items

async def fetch_market_data(query, count=10):
    """
    Асинхронно получает данные из API Яндекс Маркета.
    """
    cache_key = get_random_string(length=32)
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
        headers = {'Authorization': YANDEX_API_KEY}
    url = f'https://api.content.market.yandex.ru/v3/affiliate/search?text={query}&geo_id=213&clid=2848596&fields=MODEL_PRICE,MODEL_RATING,MODEL_DEFAULT_OFFER,OFFER_PHOTO&count={count}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=4) as response:
                response.raise_for_status()
                market_text = await response.text()
                market = json.loads(market_text)
                market = market['items']
                cache.set(cache_key, market, 300)
                return market
    except aiohttp.ClientError as e:
        return {"error": f'Ошибка запроса к API Яндекс Маркета: {e}'}
    except json.JSONDecodeError as e:
        return {"error": f'Ошибка декодирования JSON: {e}'}
    except Exception as e:
        return {"error": f'Неизвестная ошибка: {e}'}


class ItemDetailView(DetailView):
    """Представление для детальной страницы статьи."""
    model = Item
    template_name = "post.html"
    queryset = Item.objects.filter(is_published=True)

    def get(self, request, *args, **kwargs):
        """Получает объект и увеличивает счетчик просмотров."""
        self.object = self.get_object()
        self.object.views += 1
        self.object.save()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_related_items(self, obj):
      """Получает связанные статьи"""
      cat = obj.category_id
      related_items = Item.objects.filter(category__pk=cat,is_published=True).exclude(id=obj.id)[:6].prefetch_related('category')
      related_items2 = Item.objects.filter(category__pk=cat,is_published=True).exclude(id=obj.id).order_by('?')[:6].prefetch_related('category')
      return related_items, related_items2

    def get_same_category(self, obj):
        """Получает статьи из той же категории."""
        return Item.objects.filter(category=obj.category,is_published=True).exclude(id=obj.id).order_by('?')[:40].prefetch_related('category')


    def get_neighbors(self, obj):
        """Получает соседние статьи."""
        neighbors1 = Item.objects.filter(pk=int(obj.id + 1),is_published=True)
        neighbors2 = Item.objects.filter(pk=int(obj.id - 1),is_published=True)
        return neighbors1, neighbors2

    def get_context_data(self, **kwargs):
        """Формирует контекст для шаблона."""
        context = super().get_context_data(**kwargs)
        obj = self.object
        fotos = Item.objects.prefetch_related('category').order_by('title')

        context["author_arts_count"] = Item.objects.filter(author=obj.author).count()

        word_list = re.findall(r'\b\w+\b', obj.description)
        context["word_count"] = len(word_list)
        context["read_time"] = int(len(word_list)) / 650

        
        context["firstword"] = obj.title.split()[0]
        context["meta_title"] = obj.metatitle
        context["most_read"] = fotos.order_by('-views')[:4]
        
        related_items, related_items2 = self.get_related_items(obj)
        context["related_items"] = related_items
        context["related_items2"] = related_items2
        
        context["related_prod"] = Prod.objects.filter(name__icontains=obj.plitka_top)[:1]
        
        context["same_category"] = self.get_same_category(obj)

        context['category_bread_crumbs'] = obj.category.get_ancestors(include_self=True)
        
        neighbors1, neighbors2 = self.get_neighbors(obj)
        context["neighbors1"] = neighbors1
        context["neighbors2"] = neighbors2
        
        context["plitka_top"] = obj.plitka_top
        
        
        if obj.description:
            headings = re.findall(r'<h([1-6])[^>]*>(.*?)</h\1>', obj.description, re.IGNORECASE | re.DOTALL)
            if not headings:
                return ""
            toc = "<ul class='list-unstyled'>"
            for level, text in headings:
                level_int = int(level)
                indent = level_int - 1
                #Добавляем якоря автоматически, используя индекс заголовка
                anchor = f'h{level}-{headings.index((level, text))}'
                toc += f"<li><a href='#{anchor}'>{text}</a></li>"
            toc += "</ul>"
            context["toc"] = toc
            def add_anchors_to_headings(html_content):
                """Добавляет якоря к заголовкам в HTML-коде."""
                def replace_heading(match):
                    level, text = match.groups()
                    level_int = int(level)
                    anchor_id = f"h{level}-{len(added_anchors[level_int-1])}" #уникальный id
                    added_anchors[level_int -1].append(anchor_id)
                    return f'<h{level} id="{anchor_id}">{text}</h{level}>'
                added_anchors = [[] for _ in range(6)] # список для отслеживания добавленных якорей по уровням заголовков
                modified_html = re.sub(r'<h([1-6])>(.*?)</h\1>', replace_heading, html_content, flags=re.IGNORECASE | re.DOTALL)
                return modified_html
            obj.description = add_anchors_to_headings(obj.description)
            context["article"] = obj.description        
        else:
            context["toc"] = [1, 2, 3]
            context["article"] = [1, 2, 3]
        
        market_data = asyncio.run(fetch_market_data(context["firstword"]))
        if "error" in market_data:
            context["market_error"] = market_data["error"]
        else:
            context["market"] = market_data

        return context
    



class CategoryView(ListView):
    """Категория фото"""
    model = Category
    paginate_by = 33
    template_name = "posts.html"
    
    def get_queryset(self, **kwargs):
        queryset = Item.objects.all()
        category = self.kwargs['slug']
        if category is not None:
            queryset = Item.objects.filter(category__in=Category.objects.get(slug=category).get_descendants(include_self=True)).filter(is_published=True).order_by('?')
        return queryset 

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        category = self.kwargs['slug']

        cats = Category.objects.all()
        context['cats_all'] = cats.order_by('?')

        cat = Category.objects.get(slug=category)
        
        context['category_bread_crumbs'] = cat.get_ancestors(include_self=True)
        context['category_children'] = cat.get_children()
        context['cat_title'] = cat

        catt_title = cat.title
       


        
        

        plit_top = cat.plitka_top.split(',')
        shuffled_list_top = sorted(plit_top, key=lambda x: random())
        context["plitka_top"] = shuffled_list_top

        plit = cat.plitka_bottom.split(',')
        shuffled_list = sorted(plit, key=lambda x: random())
        context["plitka_bottom"] = shuffled_list        
               
        plit_search = cat.plitka_search.split(',')
        shuffled_list_s = sorted(plit_search, key=lambda x: random())
        context["plitka_search"] = shuffled_list_s

              

        

        return context




class AuthorDetailView(DetailView):
    model = Author
    template_name = "author.html"
    #queryset = Author.objects.filter(is_published=True)
    
        
    def get_context_data(self, **kwargs):
        obj = super().get_object()
        context = super().get_context_data(**kwargs)
        
        author_name = obj.id        
        arts = Item.objects.filter(author=author_name).order_by('title')
        
        context['author_arts'] = arts
        context['author_arts_count'] = arts.count()
        
        return context

class AuthorCategoryView(ListView):
    """Категория авторов"""
    model = Category
    paginate_by = 30
    template_name = "posts.html"
    
    def get_queryset(self, **kwargs):
        queryset = Item.objects.all()
        category = self.kwargs['slug']
        if category is not None:
            queryset = Item.objects.filter(category__in=Category.objects.get(slug=category).get_descendants(include_self=True)).order_by('?')
        return queryset 

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        category = self.kwargs['slug']

        cats = Category.objects.all()


              

        

        return context