from django.http import HttpResponse


def download_shopping_cart(ingredients):
    shopping_list = ['Список покупок:\n']
    for ingredient in ingredients:
        name = ingredient['ingredient__name']
        measurement_unit = ingredient['ingredient__measurement_unit']
        amount = ingredient['ingredient_amount']
        shopping_list.append(f'\n{name} - {amount}, {measurement_unit}')
    filename = 'shopping_list.txt'
    response = HttpResponse(shopping_list, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response
