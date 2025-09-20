from django.urls import path
from .views import (
    ItemDetailView,
    CategoryView,    
    AuthorDetailView
   
)
    

app_name = 'blog'

urlpatterns = [
    
    path('posts/<slug>/', CategoryView.as_view(), name='posts'),
    path('<slug>/', ItemDetailView.as_view(), name='post'),
    path('author/<slug>/', AuthorDetailView.as_view(), name='author'),
    
        
    
]
