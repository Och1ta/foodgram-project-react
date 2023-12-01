from typing import Any

from django.core.validators import RegexValidator
from rest_framework import serializers

username_regular: RegexValidator = RegexValidator(
    r'^[\w.@+-]+\Z',
    'Поддерживаются только буквы, цифры и знаки @.+-_')


class ValidateUsername:
    """Проверка username на не допустимый никнейм."""

    def validate_username(self, data: Any) -> Any:
        if data == "me":
            raise serializers.ValidationError(
                {
                    "Ошибка": "Недопустимый никнейм 'me'"
                }
            )
        return data
