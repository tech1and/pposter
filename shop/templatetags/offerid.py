from django import template
import re

register = template.Library()

@register.filter
def remove_offerid(value):
    """
    Удаляет параметр offerid и все символы после него из строки запроса URL.
    """
    if not isinstance(value, str):
        return value  # Возвращаем исходное значение, если оно не строка

    regex = r"&hid=.*"
    result = re.sub(regex, "", value)

    return result
