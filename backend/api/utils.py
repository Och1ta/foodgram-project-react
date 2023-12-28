from io import StringIO

from django.http import HttpResponse


def generate_shopping_cart(shopping_cart):
    text_stream = StringIO()
    text_stream.write('Список покупок\n')
    text_stream.write('Ингредиент - Единица измерения - Количество\n')
    lines = (' - '.join(map(str, item)) + '\n' for item in shopping_cart)
    text_stream.writelines(lines)
    response = HttpResponse(
        text_stream.getvalue(),
        content_type='text/plain')
    response['Content-Disposition'] = (
        "attachment;filename='shopping_cart.txt'"
    )
    return response
