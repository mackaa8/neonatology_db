from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from .models import Dziecko, ParametryZewnetrzne, APGARScore
from .forms import DzieckoForm, ParametryZewnetrzneForm, APGARScoreForm

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
        params_form = ParametryZewnetrzneForm(request.POST)
        apgar_form = APGARScoreForm(request.POST)

        if dziecko_form.is_valid() and params_form.is_valid() and apgar_form.is_valid():
            try:
                dziecko = dziecko_form.save()
                params = params_form.save(commit=False)
                params.dziecko = dziecko
                params.lekarz = request.user
                params.save()
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
            return render(request, 'dodaj_noworodka.html', {
                'dziecko_form': dziecko_form,
                'params_form': params_form,
                'apgar_form': apgar_form,
            })

    return render(request, 'dodaj_noworodka.html', {
        'dziecko_form': DzieckoForm(),
        'params_form': ParametryZewnetrzneForm(),
        'apgar_form': APGARScoreForm(),
    })


@login_required
def raporty(request):
    """Doctors' dashboard: list all babies and their records."""
    dzieci = Dziecko.objects.all().prefetch_related('parametry', 'apgar')

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

    return render(request, 'raporty.html', {'dzieci_status': dzieci_status})


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