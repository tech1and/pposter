from django import template
import re

register = template.Library()

@register.filter(name='clean_name')
def clean_name(value):
    """
    Убирает из строки все знаки препинания, кавычки, скобки, звездочки и оставляет только текст и цифры.
    """
    return re.sub(r'[^\w\s]', ' ', value)

