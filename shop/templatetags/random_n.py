from django import template
import random

register = template.Library()

@register.simple_tag
def random_number():
  """Возвращает случайное целое число в диапазоне от 1 до 29 (включительно)."""
  return random.randint(1, 29)