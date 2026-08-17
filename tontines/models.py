import datetime
import random
import string
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone


# Moyens de paiement mobile money disponibles au Tchad, utilisés pour les
# cotisations, les dépôts et les retraits.
MOYEN_ORANGE = 'orange_money'
MOYEN_MOOV = 'moov_money'
MOYEN_AIRTEL = 'airtel_money'
MOYEN_MTN = 'mtn_money'
MOYEN_ESPECES = 'especes'
MOYENS_MOBILE_MONEY = [
    (MOYEN_ORANGE, 'Orange Money'),
    (MOYEN_MOOV, 'Moov Money'),
    (MOYEN_AIRTEL, 'Airtel Money'),
    (MOYEN_MTN, 'MTN Money'),
]

# Pourcentage prélevé par la plateforme sur chaque retrait.
FRAIS_RETRAIT_POURCENT = 8

# Numéros de réception pour les dépôts, affichés directement à l'utilisateur.
NUMEROS_DEPOT = {
    MOYEN_AIRTEL: '86 75 25 75',
    MOYEN_MOOV: '98 58 75 97',
}

# Intérêts appliqués automatiquement sur les tontines individuelles.
TAUX_INTERET_MENSUEL = Decimal('0.05')  # 5% par période
PERIODE_INTERET_JOURS = 30


class Tontine(models.Model):
    """Une caisse de tontine gérée par un ou plusieurs administrateurs."""

    FREQUENCE_HEBDO = 'hebdomadaire'
    FREQUENCE_MENSUELLE = 'mensuelle'
    FREQUENCES = [
        (FREQUENCE_HEBDO, 'Hebdomadaire'),
        (FREQUENCE_MENSUELLE, 'Mensuelle'),
    ]

    STATUT_ACTIVE = 'active'
    STATUT_FERMEE = 'fermee'
    STATUTS = [
        (STATUT_ACTIVE, 'Active'),
        (STATUT_FERMEE, 'Fermée'),
    ]

    TYPE_INDIVIDUELLE = 'individuelle'
    TYPE_COLLECTIVE = 'collective'
    TYPES = [
        (TYPE_INDIVIDUELLE, 'Individuelle (épargne personnelle)'),
        (TYPE_COLLECTIVE, 'Collective (avec d\'autres membres)'),
    ]

    nom = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    type_tontine = models.CharField(max_length=20, choices=TYPES, default=TYPE_COLLECTIVE)
    montant_cotisation = models.DecimalField(max_digits=12, decimal_places=2, help_text="Montant en FCFA par membre et par cycle")
    frequence = models.CharField(max_length=20, choices=FREQUENCES, default=FREQUENCE_MENSUELLE)
    statut = models.CharField(max_length=20, choices=STATUTS, default=STATUT_ACTIVE)
    code_invitation = models.CharField(max_length=8, unique=True, blank=True, help_text="Code à partager pour rejoindre cette tontine")
    interets_actifs = models.BooleanField(default=True, help_text="Applique 5% d'intérêt tous les 30 jours (tontines individuelles uniquement)")
    createur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tontines_creees')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.code_invitation:
            self.code_invitation = self._generer_code_invitation()
        super().save(*args, **kwargs)

    @staticmethod
    def _generer_code_invitation():
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(alphabet, k=6))
            if not Tontine.objects.filter(code_invitation=code).exists():
                return code

    @property
    def est_individuelle(self):
        return self.type_tontine == self.TYPE_INDIVIDUELLE

    @property
    def nombre_membres(self):
        return self.adhesions.filter(actif=True).count()

    @property
    def cagnotte_par_cycle(self):
        """Montant total attendu par cycle si tous les membres cotisent."""
        return self.montant_cotisation * self.nombre_membres


class Adhesion(models.Model):
    """Lien entre un utilisateur et une tontine, avec sa position dans l'ordre de tirage."""

    tontine = models.ForeignKey(Tontine, on_delete=models.CASCADE, related_name='adhesions')
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='adhesions')
    ordre_tirage = models.PositiveIntegerField(help_text="Position dans la rotation des bénéficiaires")
    actif = models.BooleanField(default=True)
    date_adhesion = models.DateTimeField(auto_now_add=True)
    solde = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Montant accumulé sur cette tontine (épargne individuelle notamment)",
    )
    derniere_capitalisation = models.DateTimeField(default=timezone.now, help_text="Dernier point de calcul des intérêts")

    class Meta:
        unique_together = [('tontine', 'utilisateur')]
        ordering = ['ordre_tirage']

    def __str__(self):
        return f"{self.utilisateur} — {self.tontine} (#{self.ordre_tirage})"

    @property
    def prochaine_capitalisation(self):
        return self.derniere_capitalisation + datetime.timedelta(days=PERIODE_INTERET_JOURS)


class Cycle(models.Model):
    """Une période de cotisation au sein d'une tontine (ex: le mois de mars)."""

    STATUT_EN_COURS = 'en_cours'
    STATUT_TERMINE = 'termine'
    STATUTS = [
        (STATUT_EN_COURS, 'En cours'),
        (STATUT_TERMINE, 'Terminé'),
    ]

    tontine = models.ForeignKey(Tontine, on_delete=models.CASCADE, related_name='cycles')
    numero = models.PositiveIntegerField(help_text="Numéro du cycle dans la tontine (1, 2, 3...)")
    date_debut = models.DateField()
    date_fin = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUTS, default=STATUT_EN_COURS)
    beneficiaire = models.ForeignKey(
        Adhesion, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cycles_beneficies', help_text="Membre qui reçoit la cagnotte de ce cycle",
    )

    class Meta:
        unique_together = [('tontine', 'numero')]
        ordering = ['-numero']

    def __str__(self):
        return f"{self.tontine.nom} — Cycle {self.numero}"

    @property
    def total_collecte(self):
        total = self.cotisations.filter(statut=Cotisation.STATUT_PAYEE).aggregate(total=Sum('montant'))['total']
        return total or 0

    @property
    def taux_collecte(self):
        attendu = self.tontine.cagnotte_par_cycle
        if not attendu:
            return 0
        return round((self.total_collecte / attendu) * 100, 1)


class Cotisation(models.Model):
    """Le paiement d'un membre pour un cycle donné."""

    MOYENS = MOYENS_MOBILE_MONEY + [(MOYEN_ESPECES, 'Espèces')]

    STATUT_EN_ATTENTE = 'en_attente'
    STATUT_PAYEE = 'payee'
    STATUT_EN_RETARD = 'en_retard'
    STATUTS = [
        (STATUT_EN_ATTENTE, 'En attente'),
        (STATUT_PAYEE, 'Payée'),
        (STATUT_EN_RETARD, 'En retard'),
    ]

    cycle = models.ForeignKey(Cycle, on_delete=models.CASCADE, related_name='cotisations')
    adhesion = models.ForeignKey(Adhesion, on_delete=models.CASCADE, related_name='cotisations')
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    moyen_paiement = models.CharField(max_length=20, choices=MOYENS, default=MOYEN_ESPECES)
    statut = models.CharField(max_length=20, choices=STATUTS, default=STATUT_EN_ATTENTE)
    reference_transaction = models.CharField(max_length=100, blank=True, help_text="Référence de la transaction mobile money")
    date_paiement = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [('cycle', 'adhesion')]
        ordering = ['-date_paiement']

    def __str__(self):
        return f"{self.adhesion.utilisateur} — {self.cycle} — {self.get_statut_display()}"


class Depot(models.Model):
    """Demande de dépôt d'argent sur le solde de l'utilisateur via mobile money."""

    STATUT_EN_ATTENTE = 'en_attente'
    STATUT_VALIDE = 'valide'
    STATUT_REJETE = 'rejete'
    STATUTS = [
        (STATUT_EN_ATTENTE, 'En attente de validation'),
        (STATUT_VALIDE, 'Validé'),
        (STATUT_REJETE, 'Rejeté'),
    ]

    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='depots')
    tontine = models.ForeignKey(
        'Tontine', on_delete=models.CASCADE, related_name='depots',
        null=True, blank=True, help_text="Tontine concernée par ce dépôt",
    )
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    moyen_paiement = models.CharField(max_length=20, choices=MOYENS_MOBILE_MONEY)
    reference_transaction = models.CharField(max_length=100, help_text="Référence/ID de la transaction mobile money")
    statut = models.CharField(max_length=20, choices=STATUTS, default=STATUT_EN_ATTENTE)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    traite_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='depots_traites',
    )

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"Dépôt {self.montant} F — {self.utilisateur} — {self.get_statut_display()}"


class Retrait(models.Model):
    """Demande de retrait du solde de l'utilisateur, avec frais de maintien du système."""

    STATUT_EN_ATTENTE = 'en_attente'
    STATUT_VALIDE = 'valide'
    STATUT_REJETE = 'rejete'
    STATUTS = [
        (STATUT_EN_ATTENTE, 'En attente de validation'),
        (STATUT_VALIDE, 'Validé — envoyé'),
        (STATUT_REJETE, 'Rejeté — remboursé'),
    ]

    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='retraits')
    tontine = models.ForeignKey(
        'Tontine', on_delete=models.CASCADE, related_name='retraits',
        null=True, blank=True, help_text="Tontine individuelle concernée par ce retrait",
    )
    montant_demande = models.DecimalField(max_digits=12, decimal_places=2)
    frais = models.DecimalField(max_digits=12, decimal_places=2)
    montant_net = models.DecimalField(max_digits=12, decimal_places=2, help_text="Montant réellement envoyé à l'utilisateur")
    moyen_paiement = models.CharField(max_length=20, choices=MOYENS_MOBILE_MONEY)
    numero_reception = models.CharField(max_length=30, help_text="Numéro mobile money qui recevra les fonds")
    statut = models.CharField(max_length=20, choices=STATUTS, default=STATUT_EN_ATTENTE)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    traite_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='retraits_traites',
    )

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"Retrait {self.montant_demande} F — {self.utilisateur} — {self.get_statut_display()}"


class Interet(models.Model):
    """Trace chaque application d'intérêt sur une tontine individuelle."""

    adhesion = models.ForeignKey(Adhesion, on_delete=models.CASCADE, related_name='interets')
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    solde_avant = models.DecimalField(max_digits=12, decimal_places=2)
    solde_apres = models.DecimalField(max_digits=12, decimal_places=2)
    date_application = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_application']

    def __str__(self):
        return f"Intérêt {self.montant} F — {self.adhesion.utilisateur} — {self.adhesion.tontine.nom}"


class Notification(models.Model):
    """Notification affichée à un utilisateur suite à un événement (dépôt, retrait, intérêt, etc.)."""

    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    lu = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.utilisateur} — {self.message[:40]}"


def notifier(utilisateur, message):
    """Crée une notification pour un utilisateur."""
    Notification.objects.create(utilisateur=utilisateur, message=message)


def appliquer_interets(adhesion):
    """
    Capitalise les intérêts en attente pour une adhésion à une tontine individuelle.
    Rattrape automatiquement toutes les périodes de 30 jours écoulées depuis le
    dernier calcul, même si l'application n'a pas tourné entre-temps.
    """
    if adhesion.tontine.type_tontine != Tontine.TYPE_INDIVIDUELLE:
        return
    if not adhesion.tontine.interets_actifs:
        return

    maintenant = timezone.now()
    periode = datetime.timedelta(days=PERIODE_INTERET_JOURS)
    a_change = False
    garde_fou = 0

    while maintenant - adhesion.derniere_capitalisation >= periode and garde_fou < 1200:
        garde_fou += 1
        solde_avant = adhesion.solde
        montant_interet = (solde_avant * TAUX_INTERET_MENSUEL).quantize(Decimal('0.01'))
        adhesion.solde = solde_avant + montant_interet
        adhesion.derniere_capitalisation += periode
        a_change = True

        if montant_interet > 0:
            Interet.objects.create(
                adhesion=adhesion, montant=montant_interet,
                solde_avant=solde_avant, solde_apres=adhesion.solde,
            )
            notifier(
                adhesion.utilisateur,
                f"Intérêt de {montant_interet} F crédité sur votre tontine « {adhesion.tontine.nom} » "
                f"(nouveau solde : {adhesion.solde} F)."
            )

    if a_change:
        adhesion.save(update_fields=['solde', 'derniere_capitalisation'])


def appliquer_interets_toutes():
    """Rattrape les intérêts en attente pour toutes les tontines individuelles de la plateforme."""
    adhesions = Adhesion.objects.filter(
        tontine__type_tontine=Tontine.TYPE_INDIVIDUELLE, actif=True,
    ).select_related('tontine', 'utilisateur')
    for adhesion in adhesions:
        appliquer_interets(adhesion)
