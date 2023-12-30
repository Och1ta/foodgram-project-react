from io import StringIO

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response


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


def delete_model_by_recipe(request, pk, model):
    deleting_model = get_object_or_404(model.objects.filter(
        user=request.user, recipe_id=pk))
    deleting_model.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def create_serializer_by_recipe(serializer, request, pk):
    create_serializer = serializer(
        data={'user': request.user.id, 'recipe': pk},
        context={'request': request})
    create_serializer.is_valid(raise_exception=True)
    create_serializer.save()
    return Response(
        create_serializer.data, status=status.HTTP_201_CREATED
    )
