from django.contrib import admin
from .models import Tontine, Adhesion, Cycle, Cotisation, Depot, Retrait, Interet, Notification


class AdhesionInline(admin.TabularInline):
    model = Adhesion
    extra = 1


@admin.register(Tontine)
class TontineAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_tontine', 'code_invitation', 'montant_cotisation', 'frequence', 'statut', 'nombre_membres', 'createur']
    list_filter = ['statut', 'frequence', 'type_tontine']
    search_fields = ['nom', 'code_invitation']
    inlines = [AdhesionInline]


@admin.register(Cycle)
class CycleAdmin(admin.ModelAdmin):
    list_display = ['tontine', 'numero', 'date_debut', 'date_fin', 'statut', 'total_collecte', 'beneficiaire']
    list_filter = ['statut', 'tontine']


@admin.register(Cotisation)
class CotisationAdmin(admin.ModelAdmin):
    list_display = ['adhesion', 'cycle', 'montant', 'moyen_paiement', 'statut', 'date_paiement']
    list_filter = ['statut', 'moyen_paiement']
    search_fields = ['reference_transaction', 'adhesion__utilisateur__username']


@admin.register(Adhesion)
class AdhesionAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'tontine', 'ordre_tirage', 'actif', 'solde', 'derniere_capitalisation']
    list_filter = ['actif', 'tontine']


@admin.register(Interet)
class InteretAdmin(admin.ModelAdmin):
    list_display = ['adhesion', 'montant', 'solde_avant', 'solde_apres', 'date_application']
    list_filter = ['date_application']
    search_fields = ['adhesion__utilisateur__username', 'adhesion__tontine__nom']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'message', 'lu', 'date_creation']
    list_filter = ['lu']
    search_fields = ['utilisateur__username', 'message']


@admin.register(Depot)
class DepotAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'montant', 'moyen_paiement', 'statut', 'date_creation']
    list_filter = ['statut', 'moyen_paiement']
    search_fields = ['utilisateur__username', 'reference_transaction']


@admin.register(Retrait)
class RetraitAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'montant_demande', 'frais', 'montant_net', 'statut', 'date_creation']
    list_filter = ['statut', 'moyen_paiement']
    search_fields = ['utilisateur__username', 'numero_reception']
