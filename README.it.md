# APCO Weather

[Polski](README.pl.md) · [English](README.md) · **Italiano** · [Español](README.es.md)

Scheda meteo per Home Assistant dedicata ai piloti di parapendio. Scegli un punto preciso sulla mappa, imposta le soglie di vento e precipitazioni e visualizza le ore consecutive con la stessa valutazione raggruppate in finestre meteo.

Schermate del componente autonomo in inglese, con temi chiaro e scuro, acquisite il 13 novembre 2026. Varsavia usa dati dimostrativi simulati (finestra verde 07:00–14:00); Piecki mostra le previsioni Open-Meteo al momento dell’acquisizione. I dati dimostrativi non sono utilizzati dalla scheda installata.

<h3>Varsavia · tema scuro</h3>

<img src="https://raw.githubusercontent.com/piotrwozniak/apco-maniacs-card/main/docs/weather-en-dark.png" alt="Varsavia — interfaccia inglese, tema scuro" width="320" align="left" hspace="16">

Condizioni attuali e finestre meteo dei giorni successivi in un’unica vista. Le ore consecutive con la stessa valutazione formano una finestra con temperatura, vento massimo, direzione e precipitazioni.

L’esempio di Varsavia usa dati simulati, compresa la finestra verde 07:00–14:00. La scheda installata richiede sempre le previsioni per la posizione configurata.

<br clear="all">

<h3>Piecki · tema chiaro</h3>

<img src="https://raw.githubusercontent.com/piotrwozniak/apco-maniacs-card/main/docs/weather-en-light.png" alt="Piecki — interfaccia inglese, tema chiaro" width="320" align="left" hspace="16">

La scheda segue il tema attivo di Home Assistant. Gli sfondi verdi e rossi distinguono le finestre che rispettano le soglie di vento e precipitazioni da quelle che le superano.

Lo screenshot mostra le previsioni Open-Meteo acquisite per Piecki. Con il filtro diurno attivo, le finestre terminano al tramonto locale.

<br clear="all">

<h3>Scegli la tua posizione</h3>

<img src="https://raw.githubusercontent.com/piotrwozniak/apco-maniacs-card/main/docs/location-warsaw.png" alt="Selezione di Varsavia sulla mappa nell’editor di Home Assistant" width="320" align="left" hspace="16">

Apri l’editor visuale, fai clic sulla mappa o trascina il segnaposto sul decollo, quindi assegna un nome e salva la scheda. Ogni scheda ha una posizione indipendente e non modifica quella di casa in HA.

Editor reale di Home Assistant con il centro di Varsavia: 52.2297, 21.0122. Imposta separatamente il fuso orario nell’editor.

<br clear="all">

- Mappa nativa con segnaposto trascinabile nell’editor visuale; coordinate inseribili anche manualmente.
- Previsioni Open-Meteo senza entità meteo, integrazione Python o chiave API.
- Valutazione oraria, finestre senza limite di tre ore e filtro alba/tramonto.
- Polacco, inglese, italiano e spagnolo; date e numeri localizzati e temi chiari/scuri di HA.
- Un solo file da installare, senza librerie caricate da CDN.

## Integrazione Home Assistant con scheda inclusa · anteprima

APCO Weather (prima APCO Maniacs) è ora un’integrazione con scheda inclusa, dallo stesso repository. Richiede HA 2026.3+. Il ramo è un’anteprima; la versione stabile 1.0.10 usa ancora Dashboard. URL e identificatori tecnici restano compatibili. [Guida di installazione e migrazione](docs/integration/README.md).

## Installazione con HACS

1. Aggiungi `https://github.com/piotrwozniak/apco-maniacs-card` ai repository personalizzati HACS come **Integrazione** e scarica **APCO Weather**. Prima della pubblicazione usa lo ZIP di questo ramo, non la versione stabile 1.0.10.
2. Riavvia HA. Aggiungi **APCO Weather** in **Impostazioni → Dispositivi e servizi**, quindi configura nome, posizione, fuso orario e soglie.
3. Ricarica completamente il browser. L’integrazione carica automaticamente la scheda inclusa; non serve un download Dashboard o una risorsa separata.
4. Aggiungi **APCO Weather** alla dashboard e scegli il sensore **Condizioni**. Ogni posizione ha sensori di temperatura, vento, probabilità di precipitazioni e condizioni, aggiornati ogni 15 minuti anche con la dashboard chiusa.

Esempio (usa l’ID reale del sensore Condizioni):

```yaml
type: custom:apco-weather-card
entity: sensor.apco_weather_piecki_conditions
language: it
forecast_hours: 40
daylight_only: true
```

## Scegliere una posizione sulla mappa

Con un’entità selezionata, modifica posizione e soglie tramite Configura in Dispositivi e servizi. Senza entità usa la mappa della scheda descritta sotto.

Apri la dashboard → Modifica dashboard → Modifica la scheda APCO Weather. Usa l’editor visuale (passa dall’editor di codice se necessario), fai clic sulla mappa o trascina il segnaposto e salva la scheda. Lo screenshot mostra l’editor nativo di Home Assistant con Varsavia selezionata: latitudine `52.2297`, longitudine `21.0122`, fuso orario `Europe/Warsaw`.


## Lingua e localizzazione

Senza `language`, la scheda segue la lingua dell’interfaccia HA: `pl`, `en`, `it` ed `es`, incluse le varianti regionali come `it-IT` o `es-MX`. Le lingue non supportate usano l’inglese. Impostare esplicitamente una delle quattro lingue ha la precedenza sulla lingua di HA; i valori non riconosciuti ricadono sull’inglese. Puoi cambiare lingua nell’editor visuale.

Etichette, messaggi, giorni e mesi sono tradotti. In italiano i decimali usano la virgola. Gli orari seguono il fuso configurato e il formato a 24 ore. Fuori da HA la lingua predefinita è il polacco, salvo configurazione esplicita. Per la documentazione usa i collegamenti in alto: GitHub e HACS non selezionano automaticamente questi file.

## Migrazione dalla vecchia installazione manuale

Conserva le schede e una copia del loro YAML. Rimuovi solo le vecchie risorse di questo progetto (`/hacsfiles/apco-maniacs-card/...`, `/local/apco-maniacs-card/...` o `/local/warun-web/warun-card.js`). Rimuovi il vecchio download **Dashboard** da HACS, installa **lo stesso repository come Integrazione**, riavvia HA e aggiungi APCO Weather in Dispositivi e servizi. Riapri il browser.

I tipi `custom:apco-maniacs-card` e `custom:warun-card` restano supportati. Senza `entity` le schede mantengono le impostazioni e il download diretto; scegli Condizioni per i dati del server. Non sovrascrivere la configurazione HA o le voci Warun esistenti. Solo i sorgenti legacy nel repository sono stati spostati in `legacy/custom_components/`. [Aggiornamento e ripristino](docs/integration/README.md).

## Installazione manuale con un solo file

Copia [dist/apco-maniacs-card.js](dist/apco-maniacs-card.js) in `www/apco-maniacs-card/`. Aggiungi `/local/apco-maniacs-card/apco-maniacs-card.js?v=1.1.0-beta.1` come risorsa di tipo **Modulo JavaScript**. Se hai appena creato `www`, riavvia HA. Non servono CSS, traduzioni o immagini separati.

La versione sorgente in `warun-web/` funziona anche autonomamente e può essere installata con quattro file. La guida dettagliata [wdrozenie.html](wdrozenie.html) è in polacco.

## Valutazione delle condizioni

Un’ora è verde solo se vento e probabilità di precipitazioni sono **strettamente inferiori** alle soglie. Un cambiamento di valutazione, un’interruzione nei dati o il confine del giorno avvia una nuova finestra. I dati mancanti hanno una valutazione separata. La temperatura indica minimo e massimo dell’intervallo; vento e precipitazioni indicano i valori massimi. La direzione corrisponde all’ora con il vento più forte.

Con il filtro diurno, la finestra di oggi parte dall’inizio dell’ora corrente; i giorni successivi iniziano dalla prima ora intera all’alba o dopo di essa. Le finestre terminano al più tardi al tramonto. La valutazione rimane oraria anche se il tramonto cade, ad esempio, alle 17:24. Le previsioni vengono scaricate ogni 15 minuti; dati vecchi o incompleti non sono mostrati come condizioni favorevoli.

La scheda aiuta a pianificare, ma non valuta raffiche, turbolenza, termiche o effetti del terreno e non garantisce la sicurezza del volo. Le coordinate sono inviate a Open-Meteo per ottenere le previsioni. La mappa è gestita dall’editor nativo di HA.

## Supporto e video

Se la scheda ti è utile, puoi [offrirmi un caffè](https://buymeacoffee.com/piotrwoznil).

Video e altri progetti: [Piotrek Lata su YouTube](https://www.youtube.com/@piter_fly).

## Sviluppo e pubblicazione

La compilazione scrive lo stesso JS anche in `custom_components/apco_maniacs/frontend/`. HACS installa l’integrazione con la scheda dallo stesso repository. `python3 scripts/package_integration.py` genera `output/apco-weather.zip`; i rilasci allegano ZIP e JS autonomo. CI verifica la categoria `integration` e HA 2026.3/2026.11.

Serve Node.js 22 o successivo. Non ci sono dipendenze npm. I sorgenti autonomi in `warun-web/` non richiedono compilazione.

```sh
npm run build
npm test
npm run check:dist
python3 -m unittest discover -s tests
```

`npm run build` genera il file HACS includendo CSS e illustrazione. Dopo le modifiche rigenera e salva nel repository `dist/apco-maniacs-card.js`. La CI verifica i test, la corrispondenza del pacchetto con i sorgenti e la compatibilità HACS.

Prima di una nuova versione aggiorna `package.json`, rigenera `dist`, invia il commit, verifica Actions e pubblica una release con il tag corrispondente. Il workflow `Attach HACS bundle` allega il file JS.

L’installazione come repository personalizzato non richiede l’inclusione nel catalogo predefinito HACS: tale richiesta è separata. I test locali non sostituiscono una prova della mappa su un’istanza HA funzionante.

Dati meteo: [Open-Meteo](https://open-meteo.com/), [CC BY 4.0](https://open-meteo.com/en/terms). Progetto indipendente della comunità, non un prodotto ufficiale APCO Aviation. L’illustrazione è stata generata con IA usando APCO F1 MKII Azure #24 come riferimento visivo. Codice sorgente: [MIT](LICENSE).
