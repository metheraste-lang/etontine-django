from django.urls import path
from . import views

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
]
