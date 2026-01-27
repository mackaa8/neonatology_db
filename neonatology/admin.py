from django.contrib import admin
from .models import Dziecko, ParametryZewnetrzne, APGARScore


@admin.register(Dziecko)
class DzieckoAdmin(admin.ModelAdmin):
    list_display = ('imie', 'data_urodzenia', 'plec', 'pesel_matki')
    search_fields = ('imie', 'pesel_matki')
    list_filter = ('plec', 'data_urodzenia')
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
