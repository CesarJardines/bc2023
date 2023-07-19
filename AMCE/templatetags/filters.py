from django import template

register = template.Library()

@register.filter(name='zip')
def zip_lists(a, b):
  return zip(a, b)

@register.filter(name='get_list_item')
def get_list_item(list, index):
  return list[index].id_pregunta.contenido


@register.filter(name='get_list_item_id_resp')
def get_list_item_id_resp(list, index):
  return list[index]