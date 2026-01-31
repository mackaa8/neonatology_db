from django import forms
from .models import Dziecko, ParametryZewnetrzne, APGARScore, Matka


class MatkaForm(forms.ModelForm):
    class Meta:
        model = Matka
        fields = ['pesel', 'imie', 'nazwisko', 'grupa_krwi', 'konflikt_serologiczny']
        labels = {
            'pesel': 'PESEL',
            'imie': 'Imię',
            'nazwisko': 'Nazwisko',
            'grupa_krwi': 'Grupa krwi',
            'konflikt_serologiczny': 'Konflikt serologiczny'
        }


class DzieckoForm(forms.ModelForm):
    data_urodzenia = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Data urodzenia'
    )
    
    class Meta:
        model = Dziecko
        fields = ['imie', 'data_urodzenia', 'plec', 'matka']
        labels = {
            'imie': 'Imię',
            'plec': 'Płeć',
            'matka': 'Matka (opcjonalne - możesz dodać nową matkę poniżej)'
        }
    
    matka = forms.ModelChoiceField(
        queryset=Matka.objects.all(),
        required=False,
        empty_label="Wybierz istniejącą matkę lub dodaj nową poniżej",
        label='Istniejąca matka'
    )


class ParametryZewnetrzneForm(forms.ModelForm):
    class Meta:
        model = ParametryZewnetrzne
        exclude = ['dziecko', 'lekarz', 'data_pomiaru']
        labels = {
            'wzrost_cm': 'Wzrost (cm)',
            'waga_kg': 'Waga (kg)',
            'czy_wczesniak': 'Wcześniak',
            'obwod_glowy_cm': 'Obwód głowy (cm)',
            'oddechy_na_min': 'Oddechy/min',
            'natlenienie_spO2': 'Nasycenie tlenem (%)'
        }


class APGARScoreForm(forms.ModelForm):
    class Meta:
        model = APGARScore
        exclude = ['dziecko', 'lekarz', 'data_pomiaru']
        labels = {
            'apgar_1min': 'Wynik po 1 minucie',
            'apgar_5min': 'Wynik po 5 minutach',
            'apgar_10min': 'Wynik po 10 minutach'
        }
