# APCO Weather

**Polski** · [English](README.md) · [Italiano](README.it.md) · [Español](README.es.md)

Karta pogodowa Home Assistant dla paralotniarzy. Wybierz dokładne miejsce na mapie, ustaw progi wiatru i opadów, a karta połączy kolejne godziny o podobnej ocenie w czytelne okna pogodowe.

## Integracja Home Assistant z kartą w zestawie · wersja testowa

APCO Weather (wcześniej APCO Maniacs) jest teraz jedną integracją z dołączoną kartą, z tego samego repozytorium. Wymaga HA 2026.3+. Gałąź jest wersją testową; stabilne 1.0.10 nadal używa instalacji Dashboard. Adres repozytorium i identyfikatory techniczne pozostają zgodne. [Instrukcja instalacji i migracji](wdrozenie.html#integracja-apco).

## Zrzuty ekranu

Dwa osobne, bezstratne zrzuty PNG w podwójnej rozdzielczości: Warszawa w ciemnym motywie i Piecki w jasnym. Interfejs angielski. Zrzuty tego samego komponentu w podglądzie samodzielnym, wykonane 13 listopada 2026. Dane Warszawy są demonstracyjne (zielone okno 07:00–14:00); Piecki korzystają z prognozy Open-Meteo pobranej przy wykonywaniu zrzutów. Dane demonstracyjne nie są używane przez instalowaną kartę.

<h3>Warszawa · ciemny motyw</h3>

<img src="https://raw.githubusercontent.com/piotrwozniak/apco-maniacs-card/main/docs/weather-en-dark.png" alt="Warszawa — angielska karta, ciemny motyw" width="320" align="left" hspace="16">

Bieżące warunki i okna pogodowe na kolejne dni w jednym widoku. Kolejne godziny o tej samej ocenie tworzą wspólne okno z temperaturą, maksymalnym wiatrem, jego kierunkiem i opadami.

Przykład Warszawy korzysta z danych demonstracyjnych, w tym zielonego okna 07:00–14:00. Zainstalowana karta zawsze pobiera prognozę dla ustawionego miejsca.

<br clear="all">

<h3>Piecki · jasny motyw</h3>

<img src="https://raw.githubusercontent.com/piotrwozniak/apco-maniacs-card/main/docs/weather-en-light.png" alt="Piecki — angielska karta, jasny motyw" width="320" align="left" hspace="16">

Karta dopasowuje się do aktywnego motywu Home Assistant. Zielone i czerwone tło pozwala odróżnić okna spełniające ustawione progi wiatru i opadów od tych, które je przekraczają.

Zrzut pokazuje prognozę Open-Meteo pobraną dla Piecek. Przy włączonym filtrze pory lotów okna kończą się o lokalnym zachodzie słońca.

<br clear="all">

<h3>Wybierz swoje miejsce</h3>

<img src="https://raw.githubusercontent.com/piotrwozniak/apco-maniacs-card/main/docs/location-warsaw.png" alt="Wybór Warszawy na mapie w edytorze karty Home Assistant" width="320" align="left" hspace="16">

Otwórz edytor wizualny karty, kliknij mapę lub przesuń pinezkę na startowisko, a następnie nadaj nazwę i zapisz kartę. Każda karta ma własną lokalizację; lokalizacja domu w HA pozostaje bez zmian.

Rzeczywisty edytor Home Assistant z centrum Warszawy: 52.2297, 21.0122. Strefę czasową miejsca ustaw osobno w edytorze.

<br clear="all">

- Mapa z pinezką w graficznym edytorze karty; współrzędne można też wpisać ręcznie.
- Prognoza Open-Meteo dla wybranego punktu, bez encji pogodowej, integracji Python i klucza API.
- Godzinowa ocena, okna bez limitu 3 godzin, filtr wschodu i zachodu słońca.
- Języki PL, EN, IT i ES; motyw jasny i ciemny zgodny z HA.
- Jeden plik instalacyjny, bez bibliotek pobieranych z CDN.

## Instalacja przez HACS

1. Dodaj `https://github.com/piotrwozniak/apco-maniacs-card` w repozytoriach niestandardowych HACS jako **Integracja** i pobierz **APCO Weather**. Przed publikacją tej wersji użyj paczki ZIP z gałęzi zamiast stabilnego wydania 1.0.10.
2. Zrestartuj HA. W **Ustawienia → Urządzenia i usługi** dodaj **APCO Weather**, nazwij miejsce, ustaw pinezkę, strefę i progi.
3. Odśwież całkowicie przeglądarkę. Integracja ładuje dołączoną kartę automatycznie; osobny dodatek Dashboard ani wpis zasobu nie jest potrzebny.
4. Dodaj **APCO Weather** na dashboard i wybierz sensor **Warunki** w edytorze. Każde miejsce ma sensory temperatury, wiatru, prawdopodobieństwa opadów i warunków; wspólne pobieranie działa co 15 minut, również przy zamkniętym dashboardzie.

Przykład (podstaw rzeczywisty identyfikator sensora Warunki):

```yaml
type: custom:apco-weather-card
entity: sensor.apco_weather_piecki_conditions
language: pl
forecast_hours: 40
daylight_only: true
```

## Wybór miejsca na mapie

Przy wybranej encji integracji lokalizację i progi zmieniasz przez Konfiguruj w Urządzeniach i usługach. Bez encji używasz opisanej niżej mapy karty.

Otwórz dashboard → Edytuj panel → Edytuj kartę APCO Weather. Użyj edytora wizualnego (przełącz z edytora kodu, jeśli potrzeba), kliknij mapę lub przesuń pinezkę i zapisz kartę. Zrzut przedstawia natywny edytor Home Assistant z wybraną Warszawą: szerokość `52.2297`, długość `21.0122`, strefa `Europe/Warsaw`.


## Język i lokalizacja

Bez ustawienia `language` karta korzysta z języka interfejsu HA: `pl`, `en`, `it`, `es`, także wariantów regionalnych, np. `it-IT` i `es-MX`. Dla nieobsługiwanego języka włącza angielski. Jawny wybór jednego z czterech języków ma pierwszeństwo; nieznane wartości również przełączają na angielski. Nowe karty startują z językiem dopasowanym do HA, a w edytorze można go zmienić.

Tłumaczone są etykiety, komunikaty, dni tygodnia i miesiące; liczby mają przecinek w PL/IT/ES lub kropkę w EN. Czas jest wyświetlany w formacie 24-godzinnym według strefy lokalizacji. Poza HA domyślny język to polski. Język instrukcji wybierasz linkami na górze README — GitHub i HACS nie przełączają tych plików automatycznie.

## Przejście z ręcznej instalacji

Zachowaj karty dashboardu i kopię ich YAML. Usuń tylko stare zasoby tego projektu (`/hacsfiles/apco-maniacs-card/...`, `/local/apco-maniacs-card/...` lub `/local/warun-web/warun-card.js`). Usuń stary dodatek **Dashboard** z HACS, zainstaluj **to samo repozytorium jako Integrację**, zrestartuj HA i dodaj APCO Weather w Urządzeniach i usługach. Zamknij i otwórz ponownie przeglądarkę.

Typy `custom:apco-maniacs-card` i `custom:warun-card` pozostają obsługiwane. Karty bez `entity` zachowują dotychczasowe samodzielne pobieranie i ustawienia; wybierz Warunki, aby używać danych serwera. Nie nadpisuj konfiguracji HA ani wpisów starego Waruna. Jego źródła przeniesiono wyłącznie w repozytorium do `legacy/custom_components/`. [Szczegóły aktualizacji i wycofania](docs/integration/README.md).

## Instalacja ręczna jednego pliku

Skopiuj [dist/apco-maniacs-card.js](dist/apco-maniacs-card.js) do `www/apco-maniacs-card/`. Dodaj zasób `/local/apco-maniacs-card/apco-maniacs-card.js?v=1.1.0-beta.1` typu **Moduł JavaScript**. Przy pierwszym utworzeniu `www` zrestartuj HA. Nie potrzebujesz osobnych plików CSS, tłumaczeń ani grafiki.

Dotychczasowa wersja źródłowa w `warun-web/` nadal działa samodzielnie i może być wdrażana jako cztery pliki. Pełna instrukcja: [wdrozenie.html](wdrozenie.html).

## Jak karta ocenia pogodę

Godzina jest zielona tylko wtedy, gdy wiatr i prawdopodobieństwo opadów są **ściśle poniżej** ustawionych progów. Każda zmiana oceny, luka w prognozie lub granica dnia rozdziela okna. Brak danych ma osobną ocenę. Temperatura to zakres w całym oknie, a wiatr i opady to wartości maksymalne; kierunek odpowiada najsilniejszemu wiatrowi w oknie.

Przy włączonym filtrze dnia karta zaczyna od aktualnej pełnej godziny, kolejne dni od pierwszej pełnej godziny po wschodzie, i kończy okno najpóźniej o zachodzie. Ocena pogody jest godzinowa, nawet jeśli zachód wypada np. o 17:24. Pobieranie co 15 minut; przeterminowane lub niekompletne dane nie są przedstawiane jako dobre warunki.

Karta wspiera planowanie; nie ocenia turbulencji, porywów, termiki ani warunków terenowych. Nie jest gwarancją bezpiecznego lotu. Współrzędne wybranej lokalizacji są przesyłane do Open-Meteo w celu pobrania prognozy; podkład mapy jest obsługiwany przez natywny edytor HA.

## Wsparcie i filmy

Jeśli karta Ci się przydaje, możesz [postawić mi kawę](https://buymeacoffee.com/piotrwoznil).

Filmy i kolejne projekty: [Piotrek Lata — YouTube](https://www.youtube.com/@piter_fly).

## Rozwój i publikacja

Budowanie zapisuje identyczny JS także w `custom_components/apco_maniacs/frontend/`. HACS instaluje teraz integrację z dołączoną kartą z tego samego repozytorium. `python3 scripts/package_integration.py` tworzy `output/apco-weather.zip`; release dołącza ZIP i samodzielny JS. CI sprawdza kategorię `integration` oraz HA 2026.3/2026.11.

Wymagany Node.js 22 lub nowszy. Brak zależności npm i brak kroku budowania dla samego `warun-web/`.

```sh
npm run build
npm test
npm run check:dist
python3 -m unittest discover -s tests
```

`npm run build` tworzy pojedynczy plik HACS ze źródeł i osadza CSS oraz grafikę. Po każdej zmianie źródeł odtwórz i skomituj `dist/apco-maniacs-card.js`. CI sprawdza testy, zgodność paczki ze źródłami oraz zgodność z HACS.

Publiczne repozytorium: [piotrwozniak/apco-maniacs-card](https://github.com/piotrwozniak/apco-maniacs-card). Pierwsza wersja ma tag `v1.0.0`. Przed publikacją kolejnej wersji sprawdź wynik Actions. Workflow wydania dołączy ZIP integracji i samodzielny JS. Przy kolejnej wersji podnieś numer w `package.json`, odtwórz `dist`, wyślij commit i utwórz odpowiadający mu release.

Repozytorium można instalować jako niestandardowe bez zgłaszania go do domyślnego katalogu HACS. Zgłoszenie do katalogu to oddzielny krok. Bez testu na działającym HA nie traktuj lokalnych testów edytora jako potwierdzenia działania konkretnej wersji frontendu HA.

Weather data: [Open-Meteo](https://open-meteo.com/), [CC BY 4.0](https://open-meteo.com/en/terms). Independent community project, not an official APCO Aviation product. The header illustration was generated with AI using APCO F1 MKII Azure #24 as a visual reference. Source code: [MIT](LICENSE).
