from django import template
from django.http import HttpRequest

register = template.Library()


@register.inclusion_tag("django_tables2/header.html", takes_context=True)
def render_header(context: dict) -> dict:
    url = Url(context["table"].prefixed_order_by_field, context["request"])
    for column in context["table"].columns:
        sort_url, remove_sort_url, first_sort, descending = url.get_sort_url(
            column.name
        )
        column.ext = {
            "sort_url": sort_url,
            "remove_sort_url": remove_sort_url,
            "first_sort": first_sort,
            "descending": descending,
            "next": remove_sort_url if not first_sort and descending else sort_url,
        }

    return context


class Url:
    """
    Based on code from:
    https://github.com/TheRealVizard/django-table-sort/blob/main/django_table_sort/table.py
    """

    def __init__(self, sort_key_name: str, request: HttpRequest):
        self.sort_key_name = sort_key_name
        self.request = request

    def contains_field(self, lookups: list, field: str) -> int:
        """Check if the field is in the sort lookups."""
        try:
            return lookups.index(field)
        except ValueError:
            return -1

    def get_sort_url(self, field: str) -> tuple[str, str, bool, bool]:
        """Generate the urls to sort the table for the given field."""
        lookups = self.request.GET.copy()
        removed_lookup = self.request.GET.copy()

        first_sort = True
        descending = True

        if self.sort_key_name in lookups.keys():
            current_order = lookups.getlist(self.sort_key_name, [])
            removed_order = current_order.copy()
            position = self.contains_field(current_order, field)
            if position != -1:
                first_sort = False
                descending = False
                current_order[position] = f"-{field}"
                removed_order.remove(field)
            else:
                position = self.contains_field(current_order, f"-{field}")
                if position != -1:
                    first_sort = False
                    current_order[position] = field
                    removed_order.remove(f"-{field}")
                else:
                    current_order.append(field)
            lookups.setlist(self.sort_key_name, current_order)
            if len(removed_order) >= 1:
                removed_lookup.setlist(self.sort_key_name, removed_order)
            else:
                removed_lookup.pop(self.sort_key_name)
        else:
            lookups.setlist(self.sort_key_name, [field])

        return (
            lookups.urlencode(),
            removed_lookup.urlencode(),
            first_sort,
            descending,
        )
