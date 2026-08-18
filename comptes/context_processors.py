def notifications(request):
    if request.user.is_authenticated:
        from tontines.models import Notification
        compte = Notification.objects.filter(utilisateur=request.user, lu=False).count()
        return {'notifications_non_lues': compte}
    return {'notifications_non_lues': 0}
