from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re

class MinimumLengthValidator:
    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _("This password must contain at least %(min_length)d characters."),
                code='password_too_short',
                params={'min_length': self.min_length},
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least %(min_length)d characters."
            % {'min_length': self.min_length}
        )

class MinimumLetterValidator:
    def __init__(self, min_letter=1):
        self.min_letter = min_letter

    def validate(self, password, user=None):
        counter = 0;
        for x in password:
            if (ord(x) >= 97 and ord(x) <=122):
                counter = counter +1
        if counter < self.min_letter:
            raise ValidationError(
                _("Su contraseña debe contener al menos %(min_letter)d minúscula."),
                code='password_too_short',
                params={'min_letter': self.min_letter},
            )

    def get_help_text(self):
        return _(
            "Su contraseña debe contener al menos %(min_letter)d minúscula."
            % {'min_letter': self.min_letter}
        )

class MinimumNumberValidator:
    def __init__(self, min_number=1):
        self.min_number = min_number

    def validate(self, password, user=None):
        counter = 0;
        for x in password:
            if ord(x) >= 48 and ord(x) <=57:
                counter = counter +1
        if counter < self.min_number:
            raise ValidationError(
                _("Su contraseña debe contener al menos %(min_number)d número."),
                code='password_too_short',
                params={'min_number': self.min_number},
            )

    def get_help_text(self):
        return _(
            "Su contraseña debe contener al menos %(min_number)d número."
            % {'min_number': self.min_number}
        )


class MinimumCapitalaValidator:
    def __init__(self, min_capital=1):
        self.min_capital = min_capital

    def validate(self, password, user=None):
        counter = 0;
        for x in password:
            if ord(x) >= 65 and ord(x) <= 90:
                print("item", x, ord(x))
                counter = counter +1
        if counter < self.min_capital:
            raise ValidationError(
                _("Su contraseña debe contener al menos %(min_capital)d mayúscula."),
                code='password_too_short',
                params={'min_capital': self.min_capital},
            )

    def get_help_text(self):
        return _(
            "Su contraseña debe contener al menos %(min_capital)d mayúscula."
            % {'min_capital': self.min_capital}
        )

class MinimumSpecialCharactereValidator:
    def __init__(self, min_special=1):
        self.min_special = min_special
        self.example = '.!@#$%&*()_+-'

    def validate(self, password, user=None):
        if not re.findall('[.!@#$%&*()_+-]', password):
            raise ValidationError(
                _("Su contraseña debe contener al menos %(min_special)d carácter especial. ( %(example)s )"),
                code='password_too_short',
                params={'min_special': self.min_special, 'example': self.example},
            )

    def get_help_text(self):
        return _(
            "Su contraseña debe contener al menos %(min_special)d carácter especial. ( %(example)s )"
            % {'min_special': self.min_special , 'example': self.example}
        )


class Comodin:

    def validate(self, password, user=None):
        if True:
            raise ValidationError(
                _("Este error es solo un comodin"),
                code='comodin',
                params={},
            )

    def get_help_text(self):
        return _(
            "Este error es solo un comodin"
        )