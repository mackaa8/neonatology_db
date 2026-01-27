from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# --- 1. Tabela Dziecko (Baby) ---
class Dziecko(models.Model):
    imie = models.CharField(max_length=100)
    data_urodzenia = models.DateField()
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    PLEC_CHOICES = [('M', 'Mężczyzna'), ('K', 'Kobieta')]
    plec = models.CharField(max_length=1, choices=PLEC_CHOICES)
    pesel_matki = models.CharField(max_length=11, unique=True)

    def __str__(self):
        return f"{self.imie} ({self.data_urodzenia})"

# --- 2. Tabela Parametry Zewnętrzne ---
class ParametryZewnetrzne(models.Model):
    dziecko = models.ForeignKey(Dziecko, on_delete=models.CASCADE, related_name='parametry')
    lekarz = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    data_pomiaru = models.DateTimeField(auto_now_add=True)
    wzrost_cm = models.FloatField()
    waga_kg = models.FloatField()
    czy_wczesniak = models.BooleanField(default=False)
    obwod_glowy_cm = models.FloatField()
    oddechy_na_min = models.IntegerField()
    natlenienie_spO2 = models.IntegerField()

    def __str__(self):
        return f"Parametry dla {self.dziecko.imie} z {self.data_pomiaru.date()}"

# --- 3. Tabela Skala APGAR ---
class APGARScore(models.Model):
    dziecko = models.ForeignKey(Dziecko, on_delete=models.CASCADE, related_name='apgar')
    lekarz = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    data_pomiaru = models.DateTimeField(auto_now_add=True)
    apgar_1min = models.IntegerField(help_text="Wynik po 1 minucie")
    apgar_5min = models.IntegerField(help_text="Wynik po 5 minutach")
    apgar_10min = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"APGAR dla {self.dziecko.imie}: {self.apgar_5min} (5min)"
