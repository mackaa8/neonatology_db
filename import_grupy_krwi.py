import os
import csv
import django

# Konfiguracja Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neonatology_project.settings')
django.setup()

from neonatology.models import Dziecko

def importuj_grupy_krwi():
    """Importuje grupy krwi z pliku noworodki.csv do bazy danych"""

    # Liczniki
    zaktualizowane = 0
    nie_znalezione = 0
    bledne_dane = 0

    print("Rozpoczynam import grup krwi z noworodki.csv...")

    try:
        with open('noworodki.csv', 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                try:
                    # Pobierz dane z CSV
                    csv_id = int(row['id_noworodka'])
                    grupa_krwi_csv = row['grupa_krwi'].strip()

                    # Znajdź dziecko w bazie po ID
                    try:
                        dziecko = Dziecko.objects.get(id=csv_id)

                        # Zaktualizuj grupę krwi jeśli jest pusta lub różna
                        if not dziecko.grupa_krwi or dziecko.grupa_krwi != grupa_krwi_csv:
                            dziecko.grupa_krwi = grupa_krwi_csv
                            dziecko.save()
                            zaktualizowane += 1
                            print(f"Zaktualizowano: {dziecko.imie} (ID: {csv_id}) -> {grupa_krwi_csv}")
                        else:
                            print(f"Pominięto: {dziecko.imie} (ID: {csv_id}) - już ma grupę krwi")

                    except Dziecko.DoesNotExist:
                        nie_znalezione += 1
                        print(f"Nie znaleziono dziecka o ID: {csv_id}")

                except (ValueError, KeyError) as e:
                    bledne_dane += 1
                    print(f"Błędne dane w wierszu: {e}")

    except FileNotFoundError:
        print("Błąd: Plik noworodki.csv nie został znaleziony!")
        return
    except Exception as e:
        print(f"Nieoczekiwany błąd: {e}")
        return

    # Podsumowanie
    print("\n" + "="*50)
    print("PODSUMOWANIE IMPORTU:")
    print(f"Zaktualizowane dzieci: {zaktualizowane}")
    print(f"Nie znalezione dzieci: {nie_znalezione}")
    print(f"Błędne dane: {bledne_dane}")
    print("="*50)

if __name__ == "__main__":
    importuj_grupy_krwi()