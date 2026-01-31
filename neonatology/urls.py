from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('dodaj_noworodka/', views.dodaj_noworodka, name='dodaj_noworodka'),
    path('raporty/', views.raporty, name='raporty'),
    path('noworodek/<int:dziecko_id>/', views.szczegoly_noworodka, name='szczegoly_noworodka'),
    path('noworodek/<int:dziecko_id>/edytuj/', views.edytuj_dziecko, name='edytuj_dziecko'),
    path('noworodek/<int:dziecko_id>/historia/', views.historia_zmian, name='historia_zmian'),
    path('noworodek/<int:dziecko_id>/parametry/<int:param_id>/edytuj/', views.edytuj_parametry, name='edytuj_parametry'),
    path('noworodek/<int:dziecko_id>/apgar/<int:apgar_id>/edytuj/', views.edytuj_apgar, name='edytuj_apgar'),
    path('matka/<int:matka_id>/', views.szczegoly_matki, name='szczegoly_matki'),
    path('matka/<int:matka_id>/edytuj/', views.edytuj_matke, name='edytuj_matke'),
]
