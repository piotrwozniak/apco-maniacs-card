# APCO Weather · integration and dashboard card

APCO Weather (formerly APCO Maniacs) is delivered from **one repository as one Home Assistant integration containing its dashboard card**. It polls Open-Meteo every 15 minutes per location, including with the dashboard closed. No API key or existing weather entity is required. Requires HA **2026.3+**.

![APCO Weather](../../custom_components/apco_maniacs/brand/icon.png)

This feature branch is a preview; the stable 1.0.10 release still uses the older Dashboard installation. Do not select the old stable release when testing the integration. The GitHub repository URL remains unchanged. The technical domain `apco_maniacs`, existing entity IDs and old card types are retained for compatibility.

## First installation

1. Back up your HA configuration. In HACS custom repositories, use `https://github.com/piotrwozniak/apco-maniacs-card` with category **Integration** and download the integration preview when available. Before publication, use the ZIP generated from this branch and copy its `custom_components/apco_maniacs/` folder to `/config/custom_components/apco_maniacs/`.
2. Restart Home Assistant. Open **Settings → Devices & services → Add integration → APCO Weather**.
3. Enter a location name, select a native map pin, its IANA time zone and both thresholds. New entries start at the HA home coordinates without changing them. The form checks Open-Meteo before saving. Different locations can have independent entries.
4. Reload the browser fully. The integration automatically serves and loads its included card; no separate HACS Dashboard download or Lovelace resource is needed, including with YAML dashboards.
5. Add **APCO Weather** from the dashboard card picker. In its visual editor select the **Conditions** entity. Find its actual ID on the integration's device page; names below are examples.

```yaml
type: custom:apco-weather-card
entity: sensor.apco_weather_piecki_conditions
# Optional: otherwise follows the HA frontend language.
language: en
daylight_only: true
forecast_hours: 40
```

The module URL is `/apco-weather/apco-weather-card.js?v=<integration version>`. The integration loads it through HA's frontend module API, independently of how dashboard resources are managed. The module is shared by all location entries.

## Migrate an existing HACS Dashboard installation

1. Save a copy of the existing card YAML and HA configuration. Keep the dashboard cards themselves.
2. Remove only this project's old resource entries, such as `/hacsfiles/apco-maniacs-card/apco-maniacs-card.js?...`, `/local/apco-maniacs-card/apco-maniacs-card.js?...` or `/local/warun-web/warun-card.js?...`. If resources are configured in YAML, edit those specific entries there. Leave unrelated resources untouched.
3. Remove the old **Dashboard** download and its custom-repository entry from HACS, then add the **same repository** as an **Integration**, install the integration preview, restart HA and add APCO Weather in Devices & services. Catalogue/category changes are a publication step; this feature branch does not update the public catalogue automatically.
4. Fully close and reopen the frontend. Old `custom:apco-maniacs-card` and `custom:warun-card` YAML remains valid. Select a Conditions entity only on cards that should use server data. Existing cards without `entity` keep their direct Open-Meteo mode and existing location settings.

The old Warun Python integration is independent. Its source is archived under `legacy/custom_components/warun/` in the repository; its live `/config/custom_components/warun/` folder and entries should be left in place. Markdown examples are in `legacy/custom_components/md_card_place/`. Do not replace `configuration.yaml`, automations, scripts or scenes.

## Entities and settings

Each location creates one service device and four sensors:

| Sensor | Value |
| --- | --- |
| Conditions | Stable state `good`, `bad` or `unknown`, with localized display labels |
| Temperature | Current temperature, native °C |
| Wind speed | Current wind, native m/s; HA may convert its display unit |
| Precipitation probability | Probability for the current hour, % |

Only Conditions carries `apco_maniacs: true`, `forecast`, `updated_at` (UTC epoch seconds), and `location` (name, coordinates, IANA time zone and thresholds). `forecast` has Open-Meteo's structure, UTC seconds, m/s, °C and up to five days. It is excluded from Recorder attributes. Numeric sensors support history and automations. Display translations follow HA's PL/EN/IT/ES language; legacy Warun retains its separate PL/EN option.

The current assessment combines current wind with the current forecast hour's precipitation probability. Both thresholds are exclusive. Missing, invalid or stale data never produces `good`. A fetch failure makes sensors unavailable; the card can retain previous intervals with an error and its current verdict paused. It never silently switches to browser fetching. Recovery restores availability. Manual card refresh calls `homeassistant.update_entity`; all cards of a location share its polling.

Use **Configure** on the integration to change a pin, name, time zone or thresholds while preserving entity IDs. Duplicate location/time-zone entries are rejected. With `entity` selected these settings override the card's old location and thresholds. Language, forecast horizon and daylight filtering remain card settings. Clearing `entity` returns to direct browser fetching.

Forecast windows preserve the existing rules: start at the current full hour, merge adjacent equal assessments without a three-hour limit, split at gaps/local midnight/verdict changes, clip at sunset including minutes, and restart following days at the first full hour at or after sunrise.

## Updates, standalone mode and rollback

For HACS integration updates, download the new version, restart HA and fully refresh the frontend. The card updates with the integration and its URL includes the integration version. Manual installs replace only the `apco_maniacs` component folder, including `frontend/`; no separate JS copy is required. Existing entries and entity IDs remain.

The standalone alternative remains available as `dist/apco-maniacs-card.js` or the four runtime files in `warun-web/`. When using the single file independently, add it as a JavaScript module and use `custom:apco-weather-card` without `entity`. The standalone page also works without HA. Load just one build of this project's card at a time.

To roll back to stable Dashboard 1.0.10, clear `entity` from affected cards, restore a supported old card type, remove APCO Weather entries, uninstall the integration and restart HA so its frontend registration is gone. Then reinstall the old Dashboard release and its resource. Keep the dashboard cards and unrelated HA configuration.

## Branding and packaging

The original project icon combines a blue paraglider with the sun, with 256/512 px PNGs and light/dark variants under `brand/`. HA's local brand API supports these since 2026.3. Catalogue visibility also depends on the HACS/Marketplace version, publication and caches; a local icon alone does not publish a listing. This is an independent community project, not an official APCO Aviation product.

From this repository run `npm run build`, then `python3 scripts/package_integration.py`. This produces `output/apco-weather.zip`, including `custom_components/apco_maniacs/` and the bundled card, plus a staging directory under `output/apco-weather/`. This is a packaging step for the **same repository**, not a requirement for a second repository. It never writes to a live HA configuration. Release automation attaches the ZIP and standalone JS. Root HACS validation uses category `integration`.

Verification: `npm test`, `npm run check:dist`, `python3 -m unittest discover -s tests`; in Python 3.14 environments with HA 2026.3.0 or 2026.11.1 installed, `python -m unittest discover -s integration_tests`. Runtime tests run real HA config flows, entities and lifecycle, with HTTP calls and the frontend server boundary mocked. They do not visually test the native map or an installed HACS interface.

Weather: [Open-Meteo](https://open-meteo.com/), [CC BY 4.0](https://open-meteo.com/en/terms). Coordinates are sent to Open-Meteo by the HA server in integration mode or by the browser in direct mode. The public API is intended for non-commercial use. The assessment omits turbulence, gusts, thermals and terrain and is not a flight safety guarantee.

[Support the project](https://buymeacoffee.com/piotrwoznil) · [Piotrek Lata on YouTube](https://www.youtube.com/@piter_fly)
