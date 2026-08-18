from django.urls import path
from . import views

urlpatterns = [
    path('tontines/', views.liste_tontines, name='liste_tontines'),
    path('tontines/creer/', views.creer_tontine, name='creer_tontine'),
    path('tontines/<int:tontine_id>/', views.detail_tontine, name='detail_tontine'),
    path('tontines/<int:tontine_id>/rejoindre/', views.rejoindre_tontine, name='rejoindre_tontine'),
    path('tontines/<int:tontine_id>/nouveau-cycle/', views.creer_cycle, name='creer_cycle'),
    path('tontines/rejoindre-code/', views.rejoindre_par_code, name='rejoindre_par_code'),
    path('cycles/<int:cycle_id>/', views.detail_cycle, name='detail_cycle'),

    path('portefeuille/depot/', views.deposer, name='deposer'),
    path('portefeuille/retrait/', views.retirer, name='retirer'),

    path('admin-tontine/depots/<int:depot_id>/valider/', views.valider_depot, name='valider_depot'),
    path('admin-tontine/depots/<int:depot_id>/rejeter/', views.rejeter_depot, name='rejeter_depot'),
    path('admin-tontine/retraits/<int:retrait_id>/valider/', views.valider_retrait, name='valider_retrait'),
    path('admin-tontine/retraits/<int:retrait_id>/rejeter/', views.rejeter_retrait, name='rejeter_retrait'),
    path('admin-tontine/interets/recalculer/', views.recalculer_interets, name='recalculer_interets'),
    path('admin-tontine/interets/<int:tontine_id>/basculer/', views.basculer_interets, name='basculer_interets'),
]
