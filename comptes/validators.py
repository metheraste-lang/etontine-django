import re

from django.core.exceptions import ValidationError


class MotDePasseComplexeValidator:
    """
    Exige au moins un chiffre et un caractère spécial dans le mot de passe,
    en complément de la longueur minimale déjà vérifiée par MinimumLengthValidator.
    """

    def validate(self, password, user=None):
        if not re.search(r'\d', password):
            raise ValidationError(
                "Le mot de passe doit contenir au moins un chiffre.",
                code='password_no_number',
            )
        if not re.search(r'[!@#$%^&*()\-_=+\[\]{};:\'",.<>/?\\|`~]', password):
            raise ValidationError(
                "Le mot de passe doit contenir au moins un caractère spécial (ex : ! @ # $ % & *).",
                code='password_no_special',
            )

    def get_help_text(self):
        return "Votre mot de passe doit contenir au moins un chiffre et un caractère spécial."
