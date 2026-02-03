from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from .models import Dziecko, ParametryZewnetrzne, APGARScore, Matka
from .forms import DzieckoForm, ParametryZewnetrzneForm, APGARScoreForm, MatkaForm

def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'index.html')

class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True
    def get_success_url(self):
        return '/'

class CustomLogoutView(LogoutView):
    template_name = 'logout.html'
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, 'Wylogowano pomyślnie.')
        return super().dispatch(request, *args, **kwargs) 


@login_required
def dodaj_noworodka(request):
    if request.method == 'POST':
        dziecko_form = DzieckoForm(request.POST)
        matka_form = MatkaForm(request.POST)
        params_form = ParametryZewnetrzneForm(request.POST)
        apgar_form = APGARScoreForm(request.POST)

        # Sprawdź czy formularze są poprawne
        dziecko_valid = dziecko_form.is_valid()
        matka_valid = matka_form.is_valid()
        params_valid = params_form.is_valid()
        apgar_valid = apgar_form.is_valid()

        if dziecko_valid and params_valid and apgar_valid:
            try:
                # Obsługa matki
                matka = None
                if dziecko_form.cleaned_data.get('matka'):
                    # Wybrano istniejącą matkę
                    matka = dziecko_form.cleaned_data['matka']
                elif matka_valid and any(matka_form.cleaned_data.values()):
                    # Dodano nową matkę
                    matka = matka_form.save()

                # Zapisz dziecko
                dziecko = dziecko_form.save(commit=False)
                dziecko.matka = matka
                dziecko.save()

                # Zapisz parametry
                params = params_form.save(commit=False)
                params.dziecko = dziecko
                params.lekarz = request.user
                params.save()

                # Zapisz APGAR
                apgar = apgar_form.save(commit=False)
                apgar.dziecko = dziecko
                apgar.lekarz = request.user
                apgar.save()

                combined = {**dziecko_form.cleaned_data, **params_form.cleaned_data, **apgar_form.cleaned_data}
                werdykt = sprawdz_parametry(combined)
                messages.success(request, f'Noworodek {dziecko.imie} został dodany pomyślnie.')
                return render(request, 'wynik.html', {'werdykt': werdykt, 'dziecko': dziecko})
            except Exception as e:
                messages.error(request, f'Błąd: {str(e)}')
        else:
            # Jeśli formularze są nieprawidłowe, wyświetl błędy
            pass

    # GET request lub błędy walidacji
    return render(request, 'dodaj_noworodka.html', {
        'dziecko_form': DzieckoForm(),
        'matka_form': MatkaForm(),
        'params_form': ParametryZewnetrzneForm(),
        'apgar_form': APGARScoreForm(),
    })


@login_required
def raporty(request):
    """Doctors' dashboard: list all babies and their records."""
    dzieci = Dziecko.objects.all().prefetch_related('parametry', 'apgar', 'matka').order_by('-created_at')

    dzieci_status = []
    for dziecko in dzieci:
        param = dziecko.parametry.order_by('-data_pomiaru').first()
        apgar = dziecko.apgar.order_by('-data_pomiaru').first()

        # default
        status = 'Parametry w normie'

        # Hospitalizacja has highest priority
        if apgar and getattr(apgar, 'apgar_5min', None) is not None and apgar.apgar_5min < 7:
            status = 'Hospitalizacja'
        else:
            # monitoring if weight low or O2 low
            if param and ((getattr(param, 'waga_kg', None) is not None and param.waga_kg < 2.5) or (getattr(param, 'natlenienie_spO2', None) is not None and param.natlenienie_spO2 < 92)):
                status = 'Monitorowanie'

        # Build combined data dict to generate the same medical verdict used when adding a newborn
        combined = {}
        if dziecko.imie is not None:
            combined['imie'] = dziecko.imie
        if param:
            # match keys expected by sprawdz_parametry
            combined['waga_kg'] = getattr(param, 'waga_kg', None)
            combined['natlenienie_spO2'] = getattr(param, 'natlenienie_spO2', None)
        if apgar:
            combined['apgar_5min'] = getattr(apgar, 'apgar_5min', None)

        # Use the existing checker to produce a textual verdict
        werdykt = sprawdz_parametry(combined)

        # Dodaj sprawdzenie konfliktu serologicznego
        if dziecko.matka and dziecko.matka.konflikt_serologiczny and dziecko.grupa_krwi:
            # Sprawdź czy grupy krwi są różne (uproszczona logika)
            matka_grupa = dziecko.matka.grupa_krwi.lower() if dziecko.matka.grupa_krwi else ""
            dziecko_grupa = dziecko.grupa_krwi.lower()
            
            # Jeśli matka ma Rh- a dziecko Rh+, lub inne niezgodności
            if ('-' in matka_grupa and '+' in dziecko_grupa) or (matka_grupa != dziecko_grupa and matka_grupa and dziecko_grupa):
                werdykt += "\nUWAGA: Możliwy konflikt serologiczny między matką a dzieckiem!"

        dzieci_status.append({'dziecko': dziecko, 'status': status, 'werdykt': werdykt})

    # Pagination
    paginator = Paginator(dzieci_status, 50)  # 50 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'raporty.html', {'page_obj': page_obj})


@login_required
def szczegoly_noworodka(request, dziecko_id):
    """Szczegóły konkretnego noworodka."""
    dziecko = Dziecko.objects.get(id=dziecko_id)
    parametry = dziecko.parametry.all()
    apgar_scores = dziecko.apgar.all()
    return render(request, 'szczegoly_noworodka.html', {
        'dziecko': dziecko,
        'parametry': parametry,
        'apgar_scores': apgar_scores,
    })


# --- KRYTYCZNA FUNKCJA WERYFIKACJI DANYCH ---
def sprawdz_parametry(dane):
    """Implementuje logikę medyczną i zwraca zalecenia."""
    
    # Przykładowa uproszczona logika
    waga = float(dane.get('waga_kg', 0))
    apgar_5min = int(dane.get('apgar_5min', 10))
    natlenienie = int(dane.get('natlenienie_spO2', 100))
    
    zalecenie = []

    # 1. Sprawdzenie APGAR
    if apgar_5min < 7:
        zalecenie.append("Niska ocena APGAR (poniżej 7 w 5. minucie). Wymagana hospitalizacja i monitorowania.")
        
    # 2. Sprawdzenie wagi (ryzyko małej wagi urodzeniowej < 2.5 kg)
    if waga < 2.5:
        zalecenie.append(f"Niska masa urodzeniowa ({waga} kg). Niezbędne monitorowanie karmienia i przyrostów.")

    # 3. Sprawdzenie natlenienia
    if natlenienie < 92:
        zalecenie.append(f"Niskie natlenienie krwi ({natlenienie}%). Wymagane dodatkowe badania saturacji i oddechu.")
        
    if not zalecenie:
        return "Parametry w normie. Dziecko nie wymaga dodatkowej interwencji."
    
    return "UWAGA, NIEPRAWIDŁOWE PARAMETRY:\n" + "\n".join(zalecenie)


@login_required
def historia_zmian(request, dziecko_id):
    """Wyświetla historię zmian dla konkretnego dziecka."""
    dziecko = get_object_or_404(Dziecko, id=dziecko_id)
    
    # Pobierz historię dziecka
    dziecko_history = []
    for history_item in dziecko.history.all():
        changes = []
        if history_item.prev_record:
            # Porównaj z poprzednią wersją
            if history_item.imie != history_item.prev_record.imie:
                changes.append(f"Imię: '{history_item.prev_record.imie}' → '{history_item.imie}'")
            if history_item.data_urodzenia != history_item.prev_record.data_urodzenia:
                changes.append(f"Data urodzenia: {history_item.prev_record.data_urodzenia} → {history_item.data_urodzenia}")
            if history_item.plec != history_item.prev_record.plec:
                changes.append(f"Płeć: {history_item.prev_record.get_plec_display()} → {history_item.get_plec_display()}")
            if history_item.grupa_krwi != history_item.prev_record.grupa_krwi:
                changes.append(f"Grupa krwi: '{history_item.prev_record.grupa_krwi}' → '{history_item.grupa_krwi}'")
            if history_item.matka_id != history_item.prev_record.matka_id:
                prev_matka = history_item.prev_record.matka.imie + " " + history_item.prev_record.matka.nazwisko if history_item.prev_record.matka else "Brak"
                curr_matka = history_item.matka.imie + " " + history_item.matka.nazwisko if history_item.matka else "Brak"
                changes.append(f"Matka: {prev_matka} → {curr_matka}")
        else:
            # Pierwsza wersja
            changes.append(f"Pierwsza wersja - Imię: {history_item.imie}, Data urodzenia: {history_item.data_urodzenia}, Płeć: {history_item.get_plec_display()}")
        
        dziecko_history.append({
            'data': history_item.history_date,
            'lekarz': history_item.history_user,
            'typ': 'Dziecko',
            'opis': '; '.join(changes) if changes else 'Utworzenie rekordu dziecka',
            'object': history_item,
            'model_type': 'dziecko'
        })
    
    # Pobierz historię matki jeśli istnieje
    matka_history = []
    if dziecko.matka:
        for history_item in dziecko.matka.history.all():
            changes = []
            if history_item.prev_record:
                if history_item.pesel != history_item.prev_record.pesel:
                    changes.append(f"PESEL: '{history_item.prev_record.pesel}' → '{history_item.pesel}'")
                if history_item.imie != history_item.prev_record.imie:
                    changes.append(f"Imię: '{history_item.prev_record.imie}' → '{history_item.imie}'")
                if history_item.nazwisko != history_item.prev_record.nazwisko:
                    changes.append(f"Nazwisko: '{history_item.prev_record.nazwisko}' → '{history_item.nazwisko}'")
                if history_item.grupa_krwi != history_item.prev_record.grupa_krwi:
                    changes.append(f"Grupa krwi: '{history_item.prev_record.grupa_krwi}' → '{history_item.grupa_krwi}'")
                if history_item.konflikt_serologiczny != history_item.prev_record.konflikt_serologiczny:
                    prev_konflikt = "Tak" if history_item.prev_record.konflikt_serologiczny else "Nie"
                    curr_konflikt = "Tak" if history_item.konflikt_serologiczny else "Nie"
                    changes.append(f"Konflikt serologiczny: {prev_konflikt} → {curr_konflikt}")
            else:
                changes.append(f"Pierwsza wersja matki - {history_item.imie} {history_item.nazwisko}")
            
            matka_history.append({
                'data': history_item.history_date,
                'lekarz': history_item.history_user,
                'typ': 'Matka',
                'opis': '; '.join(changes) if changes else 'Utworzenie rekordu matki',
                'object': history_item,
                'model_type': 'matka'
            })
    
    # Pobierz historię parametrów
    parametry_history = []
    for param in dziecko.parametry.all():
        for history_item in param.history.all():
            parametry_history.append({
                'data': history_item.history_date,
                'lekarz': history_item.lekarz,
                'typ': 'Parametry',
                'opis': f"Waga: {history_item.waga_kg} kg, Wzrost: {history_item.wzrost_cm} cm, "
                       f"Natlenienie: {history_item.natlenienie_spO2}%, "
                       f"Oddechy: {history_item.oddechy_na_min}/min",
                'object': history_item,
                'model_type': 'parametry'
            })
    
    # Pobierz historię APGAR
    apgar_history = []
    for apgar in dziecko.apgar.all():
        for history_item in apgar.history.all():
            apgar_history.append({
                'data': history_item.history_date,
                'lekarz': history_item.lekarz,
                'typ': 'APGAR',
                'opis': f"1min: {history_item.apgar_1min}, 5min: {history_item.apgar_5min}"
                       f"{', 10min: ' + str(history_item.apgar_10min) if history_item.apgar_10min else ''}",
                'object': history_item,
                'model_type': 'apgar'
            })
    
    # Połącz i posortuj historię
    historia = dziecko_history + matka_history + parametry_history + apgar_history
    historia.sort(key=lambda x: x['data'], reverse=True)
    
    # Obsługa przywracania wersji
    if request.method == 'POST' and 'restore_version' in request.POST:
        version_id = request.POST.get('version_id')
        model_type = request.POST.get('model_type')
        
        if model_type == 'parametry':
            historical_param = ParametryZewnetrzne.history.get(id=version_id)
            # Przywróć wersję tworząc nowy rekord
            ParametryZewnetrzne.objects.create(
                dziecko=dziecko,
                lekarz=request.user,
                data_pomiaru=historical_param.data_pomiaru,
                wzrost_cm=historical_param.wzrost_cm,
                waga_kg=historical_param.waga_kg,
                czy_wczesniak=historical_param.czy_wczesniak,
                obwod_glowy_cm=historical_param.obwod_glowy_cm,
                oddechy_na_min=historical_param.oddechy_na_min,
                natlenienie_spO2=historical_param.natlenienie_spO2
            )
        elif model_type == 'apgar':
            historical_apgar = APGARScore.history.get(id=version_id)
            # Przywróć wersję tworząc nowy rekord
            APGARScore.objects.create(
                dziecko=dziecko,
                lekarz=request.user,
                data_pomiaru=historical_apgar.data_pomiaru,
                apgar_1min=historical_apgar.apgar_1min,
                apgar_5min=historical_apgar.apgar_5min,
                apgar_10min=historical_apgar.apgar_10min
            )
        
        messages.success(request, 'Wersja została przywrócona pomyślnie.')
        return HttpResponseRedirect(request.path)
    
    return render(request, 'historia_zmian.html', {
        'dziecko': dziecko,
        'historia': historia
    })

@login_required
def szczegoly_matki(request, matka_id):
    matka = get_object_or_404(Matka, id=matka_id)
    dzieci = matka.dzieci.all().order_by('-data_urodzenia')
    
    return render(request, 'szczegoly_matki.html', {
        'matka': matka,
        'dzieci': dzieci
    })

@login_required
def edytuj_dziecko(request, dziecko_id):
    dziecko = get_object_or_404(Dziecko, id=dziecko_id)
    
    if request.method == 'POST':
        form = DzieckoForm(request.POST, instance=dziecko)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dane dziecka zostały zaktualizowane.')
            return redirect('szczegoly_noworodka', dziecko_id=dziecko.id)
    else:
        form = DzieckoForm(instance=dziecko)
    
    return render(request, 'edytuj_dziecko.html', {
        'form': form,
        'dziecko': dziecko
    })

@login_required
def edytuj_matke(request, matka_id):
    matka = get_object_or_404(Matka, id=matka_id)
    
    if request.method == 'POST':
        form = MatkaForm(request.POST, instance=matka)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dane matki zostały zaktualizowane.')
            return redirect('szczegoly_matki', matka_id=matka.id)
    else:
        form = MatkaForm(instance=matka)
    
    return render(request, 'edytuj_matke.html', {
        'form': form,
        'matka': matka
    })

@login_required
def edytuj_parametry(request, dziecko_id, param_id):
    dziecko = get_object_or_404(Dziecko, id=dziecko_id)
    parametry = get_object_or_404(ParametryZewnetrzne, id=param_id, dziecko=dziecko)
    
    if request.method == 'POST':
        form = ParametryZewnetrzneForm(request.POST, instance=parametry)
        if form.is_valid():
            form.save()
            messages.success(request, 'Parametry zostały zaktualizowane.')
            return redirect('szczegoly_noworodka', dziecko_id=dziecko.id)
    else:
        form = ParametryZewnetrzneForm(instance=parametry)
    
    return render(request, 'edytuj_parametry.html', {
        'form': form,
        'dziecko': dziecko,
        'parametry': parametry
    })

@login_required
def edytuj_apgar(request, dziecko_id, apgar_id):
    dziecko = get_object_or_404(Dziecko, id=dziecko_id)
    apgar = get_object_or_404(APGARScore, id=apgar_id, dziecko=dziecko)
    
    if request.method == 'POST':
        form = APGARScoreForm(request.POST, instance=apgar)
        if form.is_valid():
            form.save()
            messages.success(request, 'Wyniki APGAR zostały zaktualizowane.')
            return redirect('szczegoly_noworodka', dziecko_id=dziecko.id)
    else:
        form = APGARScoreForm(instance=apgar)
    
    return render(request, 'edytuj_apgar.html', {
        'form': form,
        'dziecko': dziecko,
        'apgar': apgar
    })

@login_required
def panel_admina(request):
    """Panel administratora - pokazuje noworodki dodane przez aktualnego użytkownika."""
    
    # Pobierz wszystkie noworodki dodane przez aktualnego użytkownika
    dzieci_uzytkownika = Dziecko.objects.filter(
        parametry__lekarz=request.user
    ).distinct().prefetch_related('parametry', 'apgar', 'matka').order_by('-created_at')
    
    # Statystyki
    liczba_dzieci = dzieci_uzytkownika.count()
    liczba_matek = Matka.objects.filter(
        dzieci__parametry__lekarz=request.user
    ).distinct().count()
    
    # Pobierz ostatnie zmiany w historii
    ostatnie_zmiany = []
    
    # Zmiany w dzieciach
    for dziecko in dzieci_uzytkownika[:10]:  # ostatnie 10 dzieci
        for history_item in dziecko.history.all()[:5]:  # ostatnie 5 zmian na dziecko
            ostatnie_zmiany.append({
                'data': history_item.history_date,
                'typ': 'Dziecko',
                'obiekt': f"{dziecko.imie} {dziecko.matka.nazwisko if dziecko.matka else ''}",
                'opis': f"Zmiana w danych dziecka",
                'dziecko_id': dziecko.id
            })
    
    # Zmiany w parametrach
    parametry_uzytkownika = ParametryZewnetrzne.objects.filter(lekarz=request.user)
    for param in parametry_uzytkownika[:20]:  # ostatnie 20 parametrów
        for history_item in param.history.all()[:3]:  # ostatnie 3 zmiany na parametr
            ostatnie_zmiany.append({
                'data': history_item.history_date,
                'typ': 'Parametry',
                'obiekt': f"{param.dziecko.imie} {param.dziecko.matka.nazwisko if param.dziecko.matka else ''}",
                'opis': f"Waga: {history_item.waga_kg}kg, SpO2: {history_item.natlenienie_spO2}%",
                'dziecko_id': param.dziecko.id
            })
    
    # Zmiany w APGAR
    apgar_uzytkownika = APGARScore.objects.filter(lekarz=request.user)
    for apgar in apgar_uzytkownika[:20]:  # ostatnie 20 wyników APGAR
        for history_item in apgar.history.all()[:3]:  # ostatnie 3 zmiany na APGAR
            ostatnie_zmiany.append({
                'data': history_item.history_date,
                'typ': 'APGAR',
                'obiekt': f"{apgar.dziecko.imie} {apgar.dziecko.matka.nazwisko if apgar.dziecko.matka else ''}",
                'opis': f"1min: {history_item.apgar_1min}, 5min: {history_item.apgar_5min}",
                'dziecko_id': apgar.dziecko.id
            })
    
    # Sortuj ostatnie zmiany po dacie (najnowsze pierwsze)
    ostatnie_zmiany.sort(key=lambda x: x['data'], reverse=True)
    ostatnie_zmiany = ostatnie_zmiany[:20]  # tylko 20 ostatnich zmian
    
    return render(request, 'panel_admina.html', {
        'dzieci': dzieci_uzytkownika,
        'liczba_dzieci': liczba_dzieci,
        'liczba_matek': liczba_matek,
        'ostatnie_zmiany': ostatnie_zmiany
    })

@login_required
def dodaj_parametry(request, dziecko_id):
    """Dodaje nowe parametry do istniejącego dziecka."""
    dziecko = get_object_or_404(Dziecko, id=dziecko_id)
    
    if request.method == 'POST':
        form = ParametryZewnetrzneForm(request.POST)
        if form.is_valid():
            parametry = form.save(commit=False)
            parametry.dziecko = dziecko
            parametry.lekarz = request.user
            parametry.save()
            messages.success(request, 'Nowe parametry zostały dodane pomyślnie.')
            return redirect('szczegoly_noworodka', dziecko_id=dziecko.id)
    else:
        form = ParametryZewnetrzneForm()
    
    return render(request, 'dodaj_parametry.html', {
        'form': form,
        'dziecko': dziecko
    })

@login_required
def dodaj_apgar(request, dziecko_id):
    """Dodaje nowe wyniki APGAR do istniejącego dziecka."""
    dziecko = get_object_or_404(Dziecko, id=dziecko_id)
    
    if request.method == 'POST':
        form = APGARScoreForm(request.POST)
        if form.is_valid():
            apgar = form.save(commit=False)
            apgar.dziecko = dziecko
            apgar.lekarz = request.user
            apgar.save()
            messages.success(request, 'Nowe wyniki APGAR zostały dodane pomyślnie.')
            return redirect('szczegoly_noworodka', dziecko_id=dziecko.id)
    else:
        form = APGARScoreForm()
    
    return render(request, 'dodaj_apgar.html', {
        'form': form,
        'dziecko': dziecko
    })