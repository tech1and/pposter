from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from django.contrib.sitemaps import views as sitemaps_views
from django.contrib.sitemaps.views import sitemap
from django.views.decorators.cache import cache_page
from django.urls import include, path

from pposter.sitemaps import BlogItemSitemap, BlogCategorySitemap, ShopItemSitemap, ShopCategorySitemap, MagazSitemap

SITEMAP_CACHE_TIMEOUT = 86400  # 24 часа

sitemaps = {
    'posts': BlogItemSitemap,
    'allposts': BlogCategorySitemap,    
    'prod': ShopItemSitemap,
    'allprod': ShopCategorySitemap,
    'store': MagazSitemap,    
}


urlpatterns = [
    path('tinymce/', include('tinymce.urls')),
    path('admin/', admin.site.urls),
    path('', include('shop.urls', namespace='shop')),
    path('', include('magaz.urls', namespace='magaz')),
    path('', include('brands.urls', namespace='brands')),
    
	path('', include('blog.urls', namespace='blog')),
	#path('', include('turbopages.urls', namespace='turbo')),
	

    path('search/', include('search.urls', namespace='search')),
    
    path('sitemap.xml', cache_page(SITEMAP_CACHE_TIMEOUT)(sitemaps_views.index), {
        'sitemaps': sitemaps}, name='sitemap_index'),
    path('map-<section>.xml', cache_page(SITEMAP_CACHE_TIMEOUT)(sitemaps_views.sitemap), 
         {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('s/sitemap.html', sitemaps_views.sitemap, {
         'sitemaps': sitemaps, 'template_name': 'html_sitemap.html', 'content_type': 'text/html'}),
]



'''
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
'''