from django import forms
from .models import Dziecko, ParametryZewnetrzne, APGARScore, Matka


class MatkaForm(forms.ModelForm):
    class Meta:
        model = Matka
        fields = ['pesel', 'imie', 'nazwisko', 'grupa_krwi', 'konflikt_serologiczny']
        labels = {
            'pesel': 'PESEL',
            'imie': 'First Name',
            'nazwisko': 'Last Name',
            'grupa_krwi': 'Blood Type',
            'konflikt_serologiczny': 'Serological Conflict'
        }


class DzieckoForm(forms.ModelForm):
    data_urodzenia = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Date of Birth'
    )
    
    class Meta:
        model = Dziecko
        fields = ['imie', 'data_urodzenia', 'plec', 'matka']
        labels = {
            'imie': 'First Name',
            'plec': 'Gender',
            'matka': 'Mother (optional - you can add new mother below)'
        }
    
    matka = forms.ModelChoiceField(
        queryset=Matka.objects.all(),
        required=False,
        empty_label="Select existing mother or add new below",
        label='Existing Mother'
    )


class ParametryZewnetrzneForm(forms.ModelForm):
    class Meta:
        model = ParametryZewnetrzne
        exclude = ['dziecko', 'lekarz', 'data_pomiaru']
        labels = {
            'wzrost_cm': 'Height (cm)',
            'waga_kg': 'Weight (kg)',
            'czy_wczesniak': 'Premature',
            'obwod_glowy_cm': 'Head Circumference (cm)',
            'oddechy_na_min': 'Breaths/min',
            'natlenienie_spO2': 'O2 Saturation (%)'
        }


class APGARScoreForm(forms.ModelForm):
    class Meta:
        model = APGARScore
        exclude = ['dziecko', 'lekarz', 'data_pomiaru']
        labels = {
            'apgar_1min': '1 Minute Score',
            'apgar_5min': '5 Minute Score',
            'apgar_10min': '10 Minute Score'
        }
