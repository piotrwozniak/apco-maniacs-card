# Karta Markdown: Warun do latania

Wklej zawartość pliku `md_card_place` do karty Markdown w Lovelace.
Ustaw `sensor_name` na identyfikator sensora integracji Warun bez `sensor.`.
Sprawdź rzeczywisty identyfikator encji w Home Assistant.

Karta korzysta z atrybutu `forecast_raw` komponentu Warun, nie z atrybutów
encji `weather.*`. Wiatr w tych danych jest przeliczony na m/s, dlatego
`wind_convert` musi pozostać równy `1.0`.

Progi karty ustawia się osobno: `wind_threshold` (domyślnie 5 m/s)
i `precip_threshold` (domyślnie 10%). Okno jest dobre, gdy wszystkie trzy
wpisy prognozy spełniają oba progi. Liczba okien zależy od dostępnej prognozy
i opcji liczby godzin w integracji (domyślnie 40 godzin, maksymalnie 48).

Stan sensora zawiera krótką ocenę: „Warun”, „Brak warunu”, „Brak danych”
lub „Brak prognozy”. Pełny opis godzinowy znajduje się w atrybucie `opis`.

Encja `sun.sun` służy do ukrywania okien poza godzinami lotów.
