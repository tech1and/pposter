from django import template

register = template.Library()

@register.simple_tag
def replace_href():
    return """
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            var links = document.querySelectorAll('a[data-link]');
            links.forEach(function(link) {
                link.href = link.getAttribute('data-link');
            });
        });
    </script>
    """