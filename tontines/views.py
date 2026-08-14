import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Tontine, Adhesion, Cycle, Cotisation


def _peut_gerer_tontine(user, tontine):
    return user == tontine.createur or user.est_administrateur


def _designer_beneficiaire(tontine, numero_cycle):
    """
    Désigne automatiquement le bénéficiaire d'un cycle en suivant l'ordre
    de tirage des membres actifs, façon tour de rôle (rotation).
    Le cycle n°1 revient au membre ordre_tirage=1, le n°2 au suivant, etc.
    Une fois tout le monde passé, la rotation recommence.
    """
    membres_actifs = list(tontine.adhesions.filter(actif=True).order_by('ordre_tirage'))
    if not membres_actifs:
        return None
    index = (numero_cycle - 1) % len(membres_actifs)
    return membres_actifs[index]


def _calculer_date_fin(date_debut, frequence):
    if frequence == Tontine.FREQUENCE_HEBDO:
        return date_debut + datetime.timedelta(weeks=1)
    # Par défaut : mensuelle (~30 jours, simple et suffisant pour démarrer)
    return date_debut + datetime.timedelta(days=30)


@login_required
def liste_tontines(request):
    mes_tontines = Tontine.objects.filter(adhesions__utilisateur=request.user, adhesions__actif=True)
    autres_tontines = Tontine.objects.filter(statut=Tontine.STATUT_ACTIVE).exclude(id__in=mes_tontines)
    return render(request, 'tontines/liste.html', {
        'mes_tontines': mes_tontines,
        'autres_tontines': autres_tontines,
    })


@login_required
def creer_tontine(request):
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        description = request.POST.get('description', '').strip()
        montant = request.POST.get('montant_cotisation')
        frequence = request.POST.get('frequence', Tontine.FREQUENCE_MENSUELLE)

        if not nom or not montant:
            messages.error(request, "Le nom et le montant de cotisation sont obligatoires.")
        else:
            tontine = Tontine.objects.create(
                nom=nom, description=description,
                montant_cotisation=montant, frequence=frequence,
                createur=request.user,
            )
            Adhesion.objects.create(tontine=tontine, utilisateur=request.user, ordre_tirage=1)
            messages.success(request, f"La tontine « {tontine.nom} » a été créée.")
            return redirect('detail_tontine', tontine_id=tontine.id)

    return render(request, 'tontines/creer.html', {'frequences': Tontine.FREQUENCES})


@login_required
def detail_tontine(request, tontine_id):
    tontine = get_object_or_404(Tontine, id=tontine_id)
    adhesion_utilisateur = Adhesion.objects.filter(tontine=tontine, utilisateur=request.user).first()
    cycles = tontine.cycles.all()
    membres = tontine.adhesions.filter(actif=True).select_related('utilisateur')
    return render(request, 'tontines/detail.html', {
        'tontine': tontine,
        'adhesion_utilisateur': adhesion_utilisateur,
        'cycles': cycles,
        'membres': membres,
    })


@login_required
def rejoindre_tontine(request, tontine_id):
    tontine = get_object_or_404(Tontine, id=tontine_id, statut=Tontine.STATUT_ACTIVE)
    if Adhesion.objects.filter(tontine=tontine, utilisateur=request.user).exists():
        messages.info(request, "Vous êtes déjà membre de cette tontine.")
    else:
        prochain_ordre = tontine.adhesions.count() + 1
        Adhesion.objects.create(tontine=tontine, utilisateur=request.user, ordre_tirage=prochain_ordre)
        messages.success(request, f"Vous avez rejoint la tontine « {tontine.nom} ».")
    return redirect('detail_tontine', tontine_id=tontine.id)


@login_required
def creer_cycle(request, tontine_id):
    tontine = get_object_or_404(Tontine, id=tontine_id)

    if not _peut_gerer_tontine(request.user, tontine):
        messages.error(request, "Seul le créateur ou un administrateur peut créer un cycle.")
        return redirect('detail_tontine', tontine_id=tontine.id)

    if tontine.nombre_membres == 0:
        messages.error(request, "Impossible de créer un cycle : la tontine n'a aucun membre actif.")
        return redirect('detail_tontine', tontine_id=tontine.id)

    if request.method == 'POST':
        date_debut_str = request.POST.get('date_debut')
        try:
            date_debut = datetime.date.fromisoformat(date_debut_str)
        except (TypeError, ValueError):
            messages.error(request, "Date de début invalide.")
            return redirect('creer_cycle', tontine_id=tontine.id)

        date_fin = _calculer_date_fin(date_debut, tontine.frequence)
        numero = (tontine.cycles.count()) + 1
        beneficiaire = _designer_beneficiaire(tontine, numero)

        cycle = Cycle.objects.create(
            tontine=tontine, numero=numero,
            date_debut=date_debut, date_fin=date_fin,
            beneficiaire=beneficiaire,
        )

        # Une ligne de cotisation "en attente" est créée pour chaque membre actif
        Cotisation.objects.bulk_create([
            Cotisation(cycle=cycle, adhesion=adhesion, montant=tontine.montant_cotisation)
            for adhesion in tontine.adhesions.filter(actif=True)
        ])

        messages.success(
            request,
            f"Cycle {numero} créé. Bénéficiaire désigné : "
            f"{beneficiaire.utilisateur.first_name or beneficiaire.utilisateur.username}."
        )
        return redirect('detail_cycle', cycle_id=cycle.id)

    prochain_numero = tontine.cycles.count() + 1
    prochain_beneficiaire = _designer_beneficiaire(tontine, prochain_numero)
    return render(request, 'tontines/creer_cycle.html', {
        'tontine': tontine,
        'prochain_numero': prochain_numero,
        'prochain_beneficiaire': prochain_beneficiaire,
        'aujourdhui': datetime.date.today().isoformat(),
    })


@login_required
def detail_cycle(request, cycle_id):
    cycle = get_object_or_404(Cycle, id=cycle_id)
    tontine = cycle.tontine

    # Seul le créateur de la tontine (ou un administrateur) peut enregistrer des paiements
    peut_gerer = _peut_gerer_tontine(request.user, tontine)

    if request.method == 'POST' and peut_gerer:
        cotisation_id = request.POST.get('cotisation_id')
        cotisation = get_object_or_404(Cotisation, id=cotisation_id, cycle=cycle)
        cotisation.statut = Cotisation.STATUT_PAYEE
        cotisation.moyen_paiement = request.POST.get('moyen_paiement', cotisation.moyen_paiement)
        cotisation.reference_transaction = request.POST.get('reference_transaction', '')
        from django.utils import timezone
        cotisation.date_paiement = timezone.now()
        cotisation.save()
        messages.success(request, "Cotisation enregistrée comme payée.")
        return redirect('detail_cycle', cycle_id=cycle.id)

    cotisations = cycle.cotisations.select_related('adhesion__utilisateur')
    return render(request, 'tontines/cycle.html', {
        'cycle': cycle,
        'tontine': tontine,
        'cotisations': cotisations,
        'peut_gerer': peut_gerer,
        'moyens': Cotisation.MOYENS,
    })
