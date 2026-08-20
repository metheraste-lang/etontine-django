from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur


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
