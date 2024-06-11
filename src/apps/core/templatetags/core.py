from django import template

register = template.Library()


@register.filter
def verbose_name(instance):
    return instance._meta.verbose_name


@register.filter
def get_fields(instance, fields=None):
    return (
        (field, field.value_to_string(instance))
        for field in instance._meta.fields
        if not fields or field.name in fields.split(" ")
    )
