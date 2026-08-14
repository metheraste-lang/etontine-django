from django.urls import path
from . import views

urlpatterns = [
    path('', views.tableau_bord, name='accueil'),
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', views.ConnexionView.as_view(), name='connexion'),
    path('deconnexion/', views.DeconnexionView.as_view(), name='deconnexion'),
    path('tableau-de-bord/', views.tableau_bord, name='tableau_bord'),
    path('admin-tontine/', views.espace_admin, name='espace_admin'),
]
