from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import InscriptionForm


def inscription(request):
    if request.user.is_authenticated:
        return redirect('tableau_bord')

    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            utilisateur = form.save()
            login(request, utilisateur)
            messages.success(request, "Bienvenue sur E-Tontine Tchad !")
            return redirect('tableau_bord')
    else:
        form = InscriptionForm()

    return render(request, 'comptes/inscription.html', {'form': form})


class ConnexionView(LoginView):
    template_name = 'comptes/connexion.html'


class DeconnexionView(LogoutView):
    pass


@login_required
def tableau_bord(request):
    return render(request, 'comptes/tableau_bord.html')


def est_admin(user):
    return user.is_authenticated and user.est_administrateur


@user_passes_test(est_admin, login_url='connexion')
def espace_admin(request):
    from .models import Utilisateur
    membres = Utilisateur.objects.filter(role=Utilisateur.ROLE_MEMBRE).order_by('-date_creation')
    return render(request, 'comptes/espace_admin.html', {'membres': membres})
