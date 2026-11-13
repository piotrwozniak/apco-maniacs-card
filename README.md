# APCO Maniacs

**English** · [Polski](README.pl.md) · [Italiano](README.it.md) · [Español](README.es.md)

A Home Assistant weather card for paraglider pilots. Choose an exact point on the map, set wind and precipitation thresholds, and see consecutive hours with the same assessment grouped into clear weather windows.

## Screenshots

Warsaw and Piecki, with the English interface. Captured from the same component in its standalone preview on 13 November 2026. Warsaw uses simulated example data (a green window from 07:00 to 14:00); Piecki shows the Open-Meteo forecast fetched at capture time. Demo data is never used by the installed card.

![Warsaw and Piecki — English card, dark theme](docs/weather-en-dark.png)

![Warsaw and Piecki — English card, light theme](docs/weather-en-light.png)

- Native map with a draggable pin in the visual card editor; manual coordinates are also supported.
- Open-Meteo forecasts for the selected point, without a weather entity, Python integration or API key.
- Hourly assessments grouped into continuous windows, without a three-hour limit, with sunrise/sunset filtering.
- Polish, English, Italian and Spanish, including dates and number formatting; support for HA light and dark themes.
- A single installation file, with no libraries fetched from a CDN.

## Install with HACS

Repository: **https://github.com/piotrwozniak/apco-maniacs-card**.

1. Open HACS → ⋮ menu → **Custom repositories**.
2. Paste `https://github.com/piotrwozniak/apco-maniacs-card`, select **Dashboard**, and add it.
3. Find **APCO Maniacs**, download the card, and reload your browser.
4. Check dashboard resources at `/config/lovelace/resources`. HACS should register `apco-maniacs-card.js` as a JavaScript module. If you manage resources in YAML, add the path shown by HACS manually.
5. Add **APCO Maniacs** from the card picker. Click the map or drag the pin in the visual editor, enter a name, and save.

The resource path includes the repository name. For this repository it is:

```text
/hacsfiles/apco-maniacs-card/apco-maniacs-card.js
```

You can also configure the card in YAML:

```yaml
type: custom:apco-maniacs-card
name: My launch site
latitude: 53.531944
longitude: 21.385556
language: en
timezone: Europe/Warsaw
wind_threshold: 5
precip_threshold: 10
forecast_hours: 40
daylight_only: true
```

Each card stores its own location. Selecting a point does not change your Home Assistant home location. New cards initially use your HA home coordinates. When choosing a location in another time zone, also change `timezone` in the editor; it is not inferred from the map pin.

## Language and localization

Without a `language` setting, the card follows the language of the current Home Assistant frontend: `pl`, `en`, `it` and `es`, including regional variants such as `it-IT` and `es-MX`. Unsupported languages fall back to English. Explicitly selecting one of the four languages takes priority; unrecognized values also fall back to English. New cards start with the language matching the HA frontend, and the visual editor lets you change it.

Labels, messages, weekdays, month names and number formatting are localized. Polish, Italian and Spanish use decimal commas; English uses decimal points. Time labels use the configured location time zone and a 24-hour clock. Outside HA, the default language is Polish unless explicitly configured. The README language is selected with the links at the top; GitHub and HACS do not automatically switch between these language versions.

## Migrate from the older manual installation

Keep your existing Faryny/Piecki card configurations. After installing with HACS, remove the old `/local/warun-web/warun-card.js?...` resource and keep only the HACS resource. Close and reopen the page so the browser discards the old custom element definition. Both `custom:apco-maniacs-card` and `custom:warun-card` remain supported. You can leave the old files in `www/warun-web` until you have checked the new installation.

Do not replace `configuration.yaml`, automations or scenes. HACS installs only the dashboard card, without HA configuration files or the optional Warun Python integration.

## Manual single-file installation

Copy [dist/apco-maniacs-card.js](dist/apco-maniacs-card.js) to `www/apco-maniacs-card/`. Add `/local/apco-maniacs-card/apco-maniacs-card.js?v=1.0.2` as a **JavaScript module** resource. If you have just created `www`, restart HA. No separate CSS, translation or image files are required.

The source version in `warun-web/` still runs standalone and can also be deployed using four files. The detailed deployment guide, [wdrozenie.html](wdrozenie.html), is in Polish.

## How weather is assessed

An hour is green only when both wind speed and precipitation probability are **strictly below** your thresholds. A change in assessment, a gap in forecast timestamps or a calendar-day boundary starts a new window. Missing data receives a separate assessment. Temperature is shown as the range across the entire window; wind and precipitation are maxima, and the wind direction is taken from the hour with the strongest wind.

With daylight filtering enabled, today's window starts at the current full hour; subsequent days start at the first full hour at or after sunrise. Windows end no later than sunset. Weather assessment still uses hourly data even when sunset is at a time such as 17:24. Forecasts are fetched every 15 minutes; stale or incomplete data is not presented as good weather.

This card supports planning; it does not assess gusts, turbulence, thermals or terrain effects and cannot guarantee safe flying conditions. Coordinates are sent to Open-Meteo to request forecasts. The map tiles are handled by the native Home Assistant location editor.

## Support and videos

If you find the card useful, you can [buy me a coffee](https://buymeacoffee.com/piotrwoznil).

Videos and other projects: [Piotrek Lata on YouTube](https://www.youtube.com/@piter_fly).

## Development and releases

Node.js 22 or later is required. There are no npm dependencies. The standalone `warun-web/` sources need no build step.

```sh
npm run build
npm test
npm run check:dist
python3 -m unittest discover -s tests
```

`npm run build` generates the single HACS file, embedding CSS and the header illustration. Regenerate and commit `dist/apco-maniacs-card.js` after source changes. CI checks tests, bundle freshness and HACS compatibility.

Public repository: [piotrwozniak/apco-maniacs-card](https://github.com/piotrwozniak/apco-maniacs-card). Before publishing another version, bump `package.json`, regenerate `dist`, push the commit, check Actions, and publish a matching release tag. The `Attach HACS bundle` workflow attaches the single JS file.

Installation as a HACS custom repository does not require inclusion in the default HACS catalog; catalog submission is a separate step. Local editor tests do not replace testing the map on a running HA instance with your frontend version.

Weather data: [Open-Meteo](https://open-meteo.com/), [CC BY 4.0](https://open-meteo.com/en/terms). Independent community project, not an official APCO Aviation product. The header illustration was generated with AI using APCO F1 MKII Azure #24 as a visual reference. Source code: [MIT](LICENSE).
