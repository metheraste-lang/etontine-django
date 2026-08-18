from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect, get_object_or_404
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
    from tontines.models import Adhesion, Cotisation, Notification, appliquer_interets

    adhesions = Adhesion.objects.filter(utilisateur=request.user, actif=True).select_related('tontine')

    # Rattrape les intérêts en attente sur les tontines individuelles de l'utilisateur
    for adh in adhesions:
        if adh.tontine.type_tontine == 'individuelle':
            appliquer_interets(adh)

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

    notifications_recentes = Notification.objects.filter(utilisateur=request.user).order_by('-date_creation')[:5]

    return render(request, 'comptes/tableau_bord.html', {
        'adhesions': adhesions,
        'total_cotise': total_cotise,
        'nombre_tontines': adhesions.count(),
        'en_attente': en_attente,
        'journal': journal,
        'montant_collectives': sum(a.tontine.montant_cotisation for a in tontines_collectives),
        'montant_individuelles': sum(a.solde for a in tontines_individuelles),
        'notifications_recentes': notifications_recentes,
    })


def est_admin(user):
    return user.is_authenticated and user.est_administrateur


@user_passes_test(est_admin, login_url='connexion')
def espace_admin(request):
    from django.db.models import Sum
    from .models import Utilisateur
    from tontines.models import Tontine, Cotisation, Adhesion, Depot, Retrait, Interet, appliquer_interets_toutes

    # Rattrape les intérêts en attente sur toutes les tontines individuelles avant d'afficher les stats
    appliquer_interets_toutes()

    membres = list(Utilisateur.objects.order_by('-date_creation'))

    tontines = list(Tontine.objects.all().order_by('-date_creation'))
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
    ).select_related('utilisateur', 'tontine').order_by('date_creation')

    retraits_en_attente = Retrait.objects.filter(
        statut=Retrait.STATUT_EN_ATTENTE,
    ).select_related('utilisateur', 'tontine').order_by('date_creation')

    # --- Cotisations totales par membre et par tontine ---
    totaux_par_membre = {
        ligne['adhesion__utilisateur']: ligne['total']
        for ligne in Cotisation.objects.filter(statut=Cotisation.STATUT_PAYEE)
            .values('adhesion__utilisateur').annotate(total=Sum('montant'))
    }
    for m in membres:
        m.total_cotise = totaux_par_membre.get(m.id, 0)

    totaux_par_tontine = {
        ligne['cycle__tontine']: ligne['total']
        for ligne in Cotisation.objects.filter(statut=Cotisation.STATUT_PAYEE)
            .values('cycle__tontine').annotate(total=Sum('montant'))
    }
    for t in tontines:
        t.total_cotise_tontine = totaux_par_tontine.get(t.id, 0)

    # --- Dépôts et retraits validés : totaux par membre, par tontine et globaux ---
    depots_valides_par_membre = {
        ligne['utilisateur']: ligne['total']
        for ligne in Depot.objects.filter(statut=Depot.STATUT_VALIDE)
            .values('utilisateur').annotate(total=Sum('montant'))
    }
    retraits_valides_par_membre = {
        ligne['utilisateur']: ligne['total']
        for ligne in Retrait.objects.filter(statut=Retrait.STATUT_VALIDE)
            .values('utilisateur').annotate(total=Sum('montant_net'))
    }
    for m in membres:
        m.total_depose = depots_valides_par_membre.get(m.id, 0)
        m.total_retire = retraits_valides_par_membre.get(m.id, 0)

    depots_valides_par_tontine = {
        ligne['tontine']: ligne['total']
        for ligne in Depot.objects.filter(statut=Depot.STATUT_VALIDE)
            .values('tontine').annotate(total=Sum('montant'))
    }
    retraits_valides_par_tontine = {
        ligne['tontine']: ligne['total']
        for ligne in Retrait.objects.filter(statut=Retrait.STATUT_VALIDE)
            .values('tontine').annotate(total=Sum('montant_net'))
    }
    for t in tontines:
        t.total_depots_tontine = depots_valides_par_tontine.get(t.id, 0)
        t.total_retraits_tontine = retraits_valides_par_tontine.get(t.id, 0)

    # --- Répartition croisée : dépôts/retraits validés par membre ET par tontine ---
    depots_croises = Depot.objects.filter(
        statut=Depot.STATUT_VALIDE, tontine__isnull=False,
    ).values('utilisateur', 'tontine').annotate(total=Sum('montant'))

    retraits_croises = Retrait.objects.filter(
        statut=Retrait.STATUT_VALIDE, tontine__isnull=False,
    ).values('utilisateur', 'tontine').annotate(total=Sum('montant_net'))

    croise = {}
    for ligne in depots_croises:
        cle = (ligne['utilisateur'], ligne['tontine'])
        croise.setdefault(cle, {'depose': 0, 'retire': 0})
        croise[cle]['depose'] = ligne['total']
    for ligne in retraits_croises:
        cle = (ligne['utilisateur'], ligne['tontine'])
        croise.setdefault(cle, {'depose': 0, 'retire': 0})
        croise[cle]['retire'] = ligne['total']

    membres_par_id = {m.id: m for m in membres}
    tontines_par_id = {t.id: t for t in tontines}
    repartition_membre_tontine = []
    for (uid, tid), valeurs in croise.items():
        membre = membres_par_id.get(uid)
        tontine = tontines_par_id.get(tid)
        if not membre or not tontine:
            continue
        repartition_membre_tontine.append({
            'membre': membre,
            'tontine': tontine,
            'total_depose': valeurs['depose'],
            'total_retire': valeurs['retire'],
        })
    repartition_membre_tontine.sort(key=lambda ligne: (str(ligne['membre']), str(ligne['tontine'])))

    total_depots_global = Depot.objects.filter(
        statut=Depot.STATUT_VALIDE,
    ).aggregate(total=Sum('montant'))['total'] or 0

    total_retraits_global = Retrait.objects.filter(
        statut=Retrait.STATUT_VALIDE,
    ).aggregate(total=Sum('montant_net'))['total'] or 0

    # --- Historique complet des dépôts et retraits (membre + tontine visibles) ---
    historique_depots = Depot.objects.select_related('utilisateur', 'tontine').order_by('-date_creation')[:30]
    historique_retraits = Retrait.objects.select_related('utilisateur', 'tontine').order_by('-date_creation')[:30]

    # --- Contrôle des intérêts sur tontines individuelles ---
    adhesions_individuelles = Adhesion.objects.filter(
        tontine__type_tontine=Tontine.TYPE_INDIVIDUELLE, actif=True,
    ).select_related('tontine', 'utilisateur').order_by('tontine__nom')
    historique_interets = Interet.objects.select_related(
        'adhesion__utilisateur', 'adhesion__tontine'
    ).order_by('-date_application')[:20]

    return render(request, 'comptes/espace_admin.html', {
        'membres': membres,
        'nombre_membres': len(membres),
        'tontines': tontines,
        'nombre_tontines': len(tontines),
        'nombre_tontines_actives': sum(1 for t in tontines if t.statut == Tontine.STATUT_ACTIVE),
        'total_collecte': total_collecte,
        'total_depots_global': total_depots_global,
        'total_retraits_global': total_retraits_global,
        'cotisations_en_attente': cotisations_en_attente,
        'journal_global': journal_global,
        'depots_en_attente': depots_en_attente,
        'retraits_en_attente': retraits_en_attente,
        'historique_depots': historique_depots,
        'historique_retraits': historique_retraits,
        'tontines_individuelles': adhesions_individuelles,
        'historique_interets': historique_interets,
        'repartition_membre_tontine': repartition_membre_tontine,
    })


# --------------------------------------------------------------------------
# Gestion des comptes utilisateurs (réservé aux administrateurs)
# --------------------------------------------------------------------------

@user_passes_test(est_admin, login_url='connexion')
def supprimer_utilisateur(request, user_id):
    from .models import Utilisateur

    utilisateur = get_object_or_404(Utilisateur, id=user_id)

    if request.method != 'POST':
        return redirect('espace_admin')

    if utilisateur == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect('espace_admin')

    nom = str(utilisateur)
    utilisateur.delete()
    messages.success(request, f"Le compte de {nom} a été supprimé.")
    return redirect('espace_admin')


@user_passes_test(est_admin, login_url='connexion')
def reinitialiser_mot_de_passe(request, user_id):
    import secrets
    from .models import Utilisateur

    utilisateur = get_object_or_404(Utilisateur, id=user_id)

    if request.method != 'POST':
        return redirect('espace_admin')

    nouveau_mot_de_passe = secrets.token_urlsafe(6)
    utilisateur.set_password(nouveau_mot_de_passe)
    utilisateur.save()
    messages.success(
        request,
        f"Nouveau mot de passe pour {utilisateur} : {nouveau_mot_de_passe} "
        "— transmettez-le en sécurité, il ne sera plus jamais réaffiché."
    )
    return redirect('espace_admin')


@user_passes_test(est_admin, login_url='connexion')
def basculer_role(request, user_id):
    from .models import Utilisateur

    utilisateur = get_object_or_404(Utilisateur, id=user_id)

    if request.method != 'POST':
        return redirect('espace_admin')

    if utilisateur == request.user:
        messages.error(request, "Vous ne pouvez pas modifier votre propre rôle.")
        return redirect('espace_admin')

    if utilisateur.role == Utilisateur.ROLE_ADMIN:
        utilisateur.role = Utilisateur.ROLE_MEMBRE
        messages.success(request, f"{utilisateur} est maintenant un membre simple.")
    else:
        utilisateur.role = Utilisateur.ROLE_ADMIN
        messages.success(request, f"{utilisateur} est maintenant administrateur.")
    utilisateur.save()
    return redirect('espace_admin')


@user_passes_test(est_admin, login_url='connexion')
def basculer_actif(request, user_id):
    from .models import Utilisateur

    utilisateur = get_object_or_404(Utilisateur, id=user_id)

    if request.method != 'POST':
        return redirect('espace_admin')

    if utilisateur == request.user:
        messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
        return redirect('espace_admin')

    utilisateur.is_active = not utilisateur.is_active
    utilisateur.save()
    etat = "réactivé" if utilisateur.is_active else "désactivé"
    messages.success(request, f"Le compte de {utilisateur} a été {etat}.")
    return redirect('espace_admin')


@login_required
def mes_notifications(request):
    from tontines.models import Notification

    notifications = list(
        Notification.objects.filter(utilisateur=request.user).order_by('-date_creation')[:50]
    )
    Notification.objects.filter(utilisateur=request.user, lu=False).update(lu=True)

    return render(request, 'comptes/notifications.html', {'notifications': notifications})
