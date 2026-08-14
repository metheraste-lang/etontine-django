import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Cree un compte administrateur a partir de variables d'environnement, si aucun n'existe deja."

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        telephone = os.environ.get('DJANGO_SUPERUSER_TELEPHONE', '+235000000000')

        if not username or not password:
            self.stdout.write('Variables DJANGO_SUPERUSER_USERNAME / PASSWORD manquantes, etape ignoree.')
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write('Le compte administrateur existe deja.')
            return

        User.objects.create_superuser(
            username=username,
            email='',
            password=password,
            telephone=telephone,
            role=User.ROLE_ADMIN,
        )
        self.stdout.write(self.style.SUCCESS('Compte administrateur cree avec succes.'))
