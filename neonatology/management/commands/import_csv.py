import csv
from django.core.management.base import BaseCommand
from neonatology.models import Dziecko, ParametryZewnetrzne, APGARScore, Matka
from django.contrib.auth.models import User
from django.utils import timezone

class Command(BaseCommand):
    help = 'Import data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Create or get Matka
                    matka, created = Matka.objects.get_or_create(
                        pesel=row['pesel_matki'],
                        defaults={'imie': 'Unknown', 'nazwisko': 'Unknown'}
                    )
                    # Create Dziecko
                    dziecko = Dziecko.objects.create(
                        imie=row['imie'],
                        data_urodzenia=row['data_urodzenia'],
                        plec=row['plec'],
                        matka=matka
                    )
                    self.stdout.write(f'Created child: {dziecko.imie}')

                    # Create ParametryZewnetrzne
                    params = ParametryZewnetrzne.objects.create(
                        dziecko=dziecko,
                        lekarz=None,  # or get a default user
                        wzrost_cm=float(row['wzrost']),
                        waga_kg=float(row['waga']),
                        czy_wczesniak=row['wczesniak'] == '1',
                        obwod_glowy_cm=float(row['glowa']),
                        oddechy_na_min=int(row['oddechy']),
                        natlenienie_spO2=int(row['spo2'])
                    )

                    # Create APGARScore
                    apgar = APGARScore.objects.create(
                        dziecko=dziecko,
                        lekarz=None,
                        apgar_1min=int(row['apgar1']),
                        apgar_5min=int(row['apgar5']),
                        apgar_10min=int(row['apgar10']) if row['apgar10'] else None
                    )

            self.stdout.write(self.style.SUCCESS('Successfully imported data from CSV'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing data: {str(e)}'))