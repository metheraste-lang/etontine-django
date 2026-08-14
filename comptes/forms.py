from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur


class InscriptionForm(UserCreationForm):
    telephone = forms.CharField(
        label="Numéro de téléphone",
        widget=forms.TextInput(attrs={'placeholder': '+235 XX XX XX XX'}),
    )
    first_name = forms.CharField(label="Prénom", required=True)
    last_name = forms.CharField(label="Nom", required=True)

    class Meta:
        model = Utilisateur
        fields = ['first_name', 'last_name', 'telephone', 'username', 'password1', 'password2']

    def clean_telephone(self):
        telephone = self.cleaned_data['telephone']
        if Utilisateur.objects.filter(telephone=telephone).exists():
            raise forms.ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return telephone
