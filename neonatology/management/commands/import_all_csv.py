import csv
from django.core.management.base import BaseCommand
from neonatology.models import Matka, Dziecko, ParametryZewnetrzne, APGARScore
from django.utils import timezone

class Command(BaseCommand):
    help = 'Import data from CSV files: matki.csv, noworodki.csv, pomiary.csv, wyniki_apgar.csv'

    def handle(self, *args, **options):
        # Import matki
        matka_dict = {}
        with open('matki.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                matka, created = Matka.objects.get_or_create(
                    pesel=row['pesel_matki'],
                    defaults={
                        'imie': row['imie'],
                        'nazwisko': row['nazwisko'],
                        'grupa_krwi': row['grupa_krwi'],
                        'konflikt_serologiczny': False
                    }
                )
                matka_dict[row['id_matki']] = matka
        self.stdout.write(f'Imported matki: {len(matka_dict)} total')

        # Import noworodki
        dziecko_dict = {}
        with open('noworodki.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                matka = matka_dict.get(row['id_matki'])
                if matka:
                    dziecko, created = Dziecko.objects.get_or_create(
                        imie=row['imie'],
                        data_urodzenia=row['data_urodzenia'],
                        defaults={
                            'plec': row['plec'],
                            'matka': matka
                        }
                    )
                    dziecko_dict[row['id_noworodka']] = dziecko
        self.stdout.write(f'Imported noworodki: {len(dziecko_dict)} total')

        # Import pomiary
        with open('pomiary.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                dziecko = dziecko_dict.get(row['id_noworodka'])
                if dziecko:
                    ParametryZewnetrzne.objects.get_or_create(
                        dziecko=dziecko,
                        data_pomiaru=row['data_pomiaru'],
                        defaults={
                            'lekarz': None,
                            'wzrost_cm': float(row['wzrost_cm']),
                            'waga_kg': float(row['waga_g']) / 1000,
                            'czy_wczesniak': False,
                            'obwod_glowy_cm': float(row['obwod_glowy_cm']),
                            'oddechy_na_min': 30,
                            'natlenienie_spO2': 95
                        }
                    )
        self.stdout.write('Imported pomiary')

        # Import apgar
        apgar_data = {}
        with open('wyniki_apgar.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                id_noworodka = row['id_noworodka']
                minuta = int(row['minuta'])
                wynik = int(row['wynik'])
                if id_noworodka not in apgar_data:
                    apgar_data[id_noworodka] = {}
                apgar_data[id_noworodka][minuta] = wynik

        for id_noworodka, mins in apgar_data.items():
            dziecko = dziecko_dict.get(id_noworodka)
            if dziecko:
                APGARScore.objects.get_or_create(
                    dziecko=dziecko,
                    apgar_1min=mins.get(1),
                    defaults={
                        'lekarz': None,
                        'data_pomiaru': timezone.now(),
                        'apgar_5min': mins.get(5),
                        'apgar_10min': mins.get(10)
                    }
                )
        self.stdout.write('Imported apgar')

        self.stdout.write(self.style.SUCCESS('Successfully imported all data from CSV files'))