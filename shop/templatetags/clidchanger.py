from django import template

register = template.Library()

@register.filter
def replace_clid(value):
    """
    Заменяет 3807594 на 11567790 в строке.
    """
    if isinstance(value, str):
        return value.replace('3807594', '2443065')
    return value  # Возвращаем исходное значение, если оно не строка