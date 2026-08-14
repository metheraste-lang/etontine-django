from django.urls import path
from . import views

urlpatterns = [
    path('tontines/', views.liste_tontines, name='liste_tontines'),
    path('tontines/creer/', views.creer_tontine, name='creer_tontine'),
    path('tontines/<int:tontine_id>/', views.detail_tontine, name='detail_tontine'),
    path('tontines/<int:tontine_id>/rejoindre/', views.rejoindre_tontine, name='rejoindre_tontine'),
    path('tontines/<int:tontine_id>/nouveau-cycle/', views.creer_cycle, name='creer_cycle'),
    path('cycles/<int:cycle_id>/', views.detail_cycle, name='detail_cycle'),
]
