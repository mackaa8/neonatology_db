from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from .models import Dziecko, ParametryZewnetrzne, APGARScore
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
    historia = parametry_history + apgar_history
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