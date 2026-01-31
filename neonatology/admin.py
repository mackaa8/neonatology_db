from django.contrib import admin
from .models import Dziecko, ParametryZewnetrzne, APGARScore, Matka


@admin.register(Matka)
class MatkaAdmin(admin.ModelAdmin):
    list_display = ('imie', 'nazwisko', 'pesel', 'grupa_krwi')
    search_fields = ('imie', 'nazwisko', 'pesel')
    list_filter = ('grupa_krwi', 'konflikt_serologiczny')


@admin.register(Dziecko)
class DzieckoAdmin(admin.ModelAdmin):
    list_display = ('imie', 'data_urodzenia', 'plec', 'matka')
    search_fields = ('imie', 'matka__pesel', 'matka__imie', 'matka__nazwisko')
    list_filter = ('plec', 'data_urodzenia', 'matka')
    readonly_fields = ('id',)


@admin.register(ParametryZewnetrzne)
class ParametryZewnetrzneAdmin(admin.ModelAdmin):
    list_display = ('dziecko', 'data_pomiaru', 'waga_kg', 'wzrost_cm', 'lekarz')
    search_fields = ('dziecko__imie',)
    list_filter = ('data_pomiaru', 'czy_wczesniak', 'lekarz')
    readonly_fields = ('data_pomiaru',)


@admin.register(APGARScore)
class APGARScoreAdmin(admin.ModelAdmin):
    list_display = ('dziecko', 'data_pomiaru', 'apgar_1min', 'apgar_5min', 'apgar_10min', 'lekarz')
    search_fields = ('dziecko__imie',)
    list_filter = ('data_pomiaru', 'lekarz')
    readonly_fields = ('data_pomiaru',)
