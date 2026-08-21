from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from .models import Utilisateur


class PasswordResetFormDiagnostic(PasswordResetForm):
    """
    Version temporaire de diagnostic : affiche dans les logs Render
    combien de comptes correspondent à l'e-mail saisi, et pourquoi
    un compte pourrait être exclu (inactif, mot de passe invalide).
    """

    def save(self, *args, **kwargs):
        email = self.cleaned_data['email']
        utilisateurs = list(self.get_users(email))
        print(f"### DIAGNOSTIC RESET MDP : email recherche = {email!r}")
        print(f"### DIAGNOSTIC RESET MDP : {len(utilisateurs)} compte(s) trouve(s) par get_users()")

        tous = Utilisateur.objects.filter(email__iexact=email)
        print(f"### DIAGNOSTIC RESET MDP : {tous.count()} compte(s) avec cet email en base (sans filtre actif)")
        for u in tous:
            print(
                f"### DIAGNOSTIC RESET MDP : compte={u.username!r} email_exact={u.email!r} "
                f"is_active={u.is_active} mot_de_passe_utilisable={u.has_usable_password()}"
            )
        return super().save(*args, **kwargs)


class InscriptionForm(UserCreationForm):
    telephone = forms.CharField(
        label="Numéro de téléphone",
        widget=forms.TextInput(attrs={'placeholder': '+235 XX XX XX XX'}),
    )
    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={'placeholder': 'vous@exemple.com'}),
        help_text="Utilisée pour réinitialiser votre mot de passe en cas d'oubli.",
    )
    first_name = forms.CharField(label="Prénom", required=True)
    last_name = forms.CharField(label="Nom", required=True)

    class Meta:
        model = Utilisateur
        fields = ['first_name', 'last_name', 'telephone', 'email', 'username', 'password1', 'password2']

    def clean_telephone(self):
        telephone = self.cleaned_data['telephone']
        if Utilisateur.objects.filter(telephone=telephone).exists():
            raise forms.ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return telephone

    def clean_email(self):
        email = self.cleaned_data['email']
        if Utilisateur.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Cette adresse e-mail est déjà utilisée.")
        return email
