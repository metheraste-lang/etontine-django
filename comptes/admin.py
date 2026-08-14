from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    model = Utilisateur
    list_display = ['username', 'telephone', 'first_name', 'last_name', 'role', 'is_active', 'date_creation']
    list_filter = ['role', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Informations E-Tontine', {'fields': ('telephone', 'role')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations E-Tontine', {'fields': ('telephone', 'role')}),
    )
