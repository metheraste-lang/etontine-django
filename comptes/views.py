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
    from django.db.models import Sum
    from tontines.models import Adhesion, Cotisation

    adhesions = Adhesion.objects.filter(utilisateur=request.user, actif=True).select_related('tontine')

    total_cotise = Cotisation.objects.filter(
        adhesion__utilisateur=request.user,
        statut=Cotisation.STATUT_PAYEE,
    ).aggregate(total=Sum('montant'))['total'] or 0

    en_attente = Cotisation.objects.filter(
        adhesion__utilisateur=request.user,
        statut__in=[Cotisation.STATUT_EN_ATTENTE, Cotisation.STATUT_EN_RETARD],
    ).count()

    journal = Cotisation.objects.filter(
        adhesion__utilisateur=request.user,
    ).select_related('cycle__tontine').order_by('-id')[:8]

    tontines_collectives = adhesions.filter(tontine__type_tontine='collective')
    tontines_individuelles = adhesions.filter(tontine__type_tontine='individuelle')

    return render(request, 'comptes/tableau_bord.html', {
        'adhesions': adhesions,
        'total_cotise': total_cotise,
        'nombre_tontines': adhesions.count(),
        'en_attente': en_attente,
        'journal': journal,
        'montant_collectives': sum(a.tontine.montant_cotisation for a in tontines_collectives),
        'montant_individuelles': sum(a.tontine.montant_cotisation for a in tontines_individuelles),
    })


def est_admin(user):
    return user.is_authenticated and user.est_administrateur


@user_passes_test(est_admin, login_url='connexion')
def espace_admin(request):
    from django.db.models import Sum
    from .models import Utilisateur
    from tontines.models import Tontine, Cotisation, Adhesion, Depot, Retrait

    membres = Utilisateur.objects.order_by('-date_creation')

    tontines = Tontine.objects.all().order_by('-date_creation')
    total_collecte = Cotisation.objects.filter(
        statut=Cotisation.STATUT_PAYEE,
    ).aggregate(total=Sum('montant'))['total'] or 0

    cotisations_en_attente = Cotisation.objects.filter(
        statut__in=[Cotisation.STATUT_EN_ATTENTE, Cotisation.STATUT_EN_RETARD],
    ).count()

    journal_global = Cotisation.objects.select_related(
        'cycle__tontine', 'adhesion__utilisateur'
    ).order_by('-id')[:15]

    depots_en_attente = Depot.objects.filter(
        statut=Depot.STATUT_EN_ATTENTE,
    ).select_related('utilisateur').order_by('date_creation')

    retraits_en_attente = Retrait.objects.filter(
        statut=Retrait.STATUT_EN_ATTENTE,
    ).select_related('utilisateur').order_by('date_creation')

    return render(request, 'comptes/espace_admin.html', {
        'membres': membres,
        'nombre_membres': membres.count(),
        'tontines': tontines,
        'nombre_tontines': tontines.count(),
        'nombre_tontines_actives': tontines.filter(statut=Tontine.STATUT_ACTIVE).count(),
        'total_collecte': total_collecte,
        'cotisations_en_attente': cotisations_en_attente,
        'journal_global': journal_global,
        'depots_en_attente': depots_en_attente,
        'retraits_en_attente': retraits_en_attente,
    })
