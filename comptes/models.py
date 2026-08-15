from django.contrib.auth.models import AbstractUser
from django.db import models


class Utilisateur(AbstractUser):
    """
    Utilisateur personnalisé pour E-Tontine Tchad.
    Ajoute un numéro de téléphone (identifiant courant en Afrique)
    et un rôle (membre / administrateur).
    """

    ROLE_MEMBRE = 'membre'
    ROLE_ADMIN = 'administrateur'
    ROLES = [
        (ROLE_MEMBRE, 'Membre'),
        (ROLE_ADMIN, 'Administrateur'),
    ]

    telephone = models.CharField(
        max_length=20,
        unique=True,
        help_text="Numéro de téléphone (ex: +235 XX XX XX XX)",
    )
    role = models.CharField(max_length=20, choices=ROLES, default=ROLE_MEMBRE)
    solde = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Solde disponible en FCFA")
    date_creation = models.DateTimeField(auto_now_add=True)

    @property
    def est_administrateur(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.telephone})"
