from django.contrib.sitemaps import Sitemap
from blog.models import Item as BlogItem, Category as BlogCategory
from shop.models import Item as ShopItem, Category as ShopCategory
from magaz.models import Magaz


import datetime

DATE_TIME = datetime.date.today()



class BlogItemSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9
    limit = 10000
    protocol = 'https'

    def items(self):
        return BlogItem.objects.filter(is_published=True).prefetch_related('category')
        
    def lastmod(self, obj):
        return DATE_TIME
        
        
class BlogCategorySitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9
    limit = 10000
    protocol = 'https'

    def items(self):
        return BlogCategory.objects.all()
        
    def lastmod(self, obj):
        return DATE_TIME

    
    

class ShopCategorySitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9
    limit = 10000
    protocol = 'https'

    def items(self):
        return ShopCategory.objects.all()
        
    def lastmod(self, obj):
        return DATE_TIME
        
       
      

class MagazSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9
    limit = 10000
    protocol = 'https'

    def items(self):
        return Magaz.objects.all()
        
    def lastmod(self, obj):
        return DATE_TIME
        
class ShopItemSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9
    limit = 10000
    protocol = 'https'

    def items(self):
        return ShopItem.objects.all()
        
         