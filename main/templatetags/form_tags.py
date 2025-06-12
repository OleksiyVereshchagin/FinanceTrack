# from django import template
#
# register = template.Library()
#
# @register.filter(name='add_class')
# def add_class(field, css_class):
#     return field.as_widget(attrs={"class": css_class})


from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    existing_classes = field.field.widget.attrs.get('class', '')
    classes = (existing_classes + ' ' + css_class).strip()
    return field.as_widget(attrs={'class': classes})
