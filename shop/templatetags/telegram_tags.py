from django import template
import random

register = template.Library()

TELEGRAM_POSTS = [    
    "gardenmotor/448",        
    "gardenmotor/448", 
    "gardenmotor/448", 
]

@register.simple_tag
def random_telegram_post():
    """Возвращает случайный data-telegram-post."""
    return random.choice(TELEGRAM_POSTS)

