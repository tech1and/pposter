from django.urls import path
from .views import CategoryView, ItemDetailView, HomeView, AddComment


app_name = 'shop'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('c/<slug>/', CategoryView.as_view(), name='category'),
    path('i/<slug>/', ItemDetailView.as_view(), name='product'),
    path('comment/<int:pk>/', AddComment.as_view(), name='addcomment'),
]
