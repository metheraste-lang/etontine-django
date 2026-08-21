from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import PasswordResetFormDiagnostic

urlpatterns = [
    path('', views.tableau_bord, name='accueil'),
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', views.ConnexionView.as_view(), name='connexion'),
    path('deconnexion/', views.DeconnexionView.as_view(), name='deconnexion'),
    path('tableau-de-bord/', views.tableau_bord, name='tableau_bord'),
    path('admin-tontine/', views.espace_admin, name='espace_admin'),
    path('admin-tontine/utilisateurs/<int:user_id>/supprimer/', views.supprimer_utilisateur, name='supprimer_utilisateur'),
    path('admin-tontine/utilisateurs/<int:user_id>/reinitialiser/', views.reinitialiser_mot_de_passe, name='reinitialiser_mot_de_passe'),
    path('admin-tontine/utilisateurs/<int:user_id>/role/', views.basculer_role, name='basculer_role'),
    path('admin-tontine/utilisateurs/<int:user_id>/statut/', views.basculer_actif, name='basculer_actif'),
    path('notifications/', views.mes_notifications, name='notifications'),

    # Réinitialisation du mot de passe par e-mail
    path(
        'mot-de-passe-oublie/',
        auth_views.PasswordResetView.as_view(
            template_name='comptes/mot_de_passe_oublie.html',
            email_template_name='comptes/email_reinitialisation.txt',
            subject_template_name='comptes/email_reinitialisation_sujet.txt',
            success_url='/mot-de-passe-oublie/envoye/',
            form_class=PasswordResetFormDiagnostic,
        ),
        name='password_reset',
    ),
    path(
        'mot-de-passe-oublie/envoye/',
        auth_views.PasswordResetDoneView.as_view(template_name='comptes/mot_de_passe_oublie_envoye.html'),
        name='password_reset_done',
    ),
    path(
        'reinitialiser/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='comptes/reinitialiser_mot_de_passe.html',
            success_url='/reinitialiser/termine/',
        ),
        name='password_reset_confirm',
    ),
    path(
        'reinitialiser/termine/',
        auth_views.PasswordResetCompleteView.as_view(template_name='comptes/reinitialiser_mot_de_passe_termine.html'),
        name='password_reset_complete',
    ),
]
