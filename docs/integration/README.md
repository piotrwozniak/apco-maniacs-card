# APCO Maniacs integration · preview

Optional Home Assistant backend for the [APCO Maniacs weather card](https://github.com/piotrwozniak/apco-maniacs-card). It polls Open-Meteo every 15 minutes per location, even when no dashboard is open. No API key or existing weather entity is required.

![APCO Maniacs](../../custom_components/apco_maniacs/brand/icon.png)

Requires Home Assistant **2026.3 or newer**. This is a feature preview, not a published HACS integration. The card repository remains a HACS Dashboard/plugin. A separate integration repository is required before offering this backend through HACS; do not add the card repository again as an Integration. The export script prepares that repository's layout with exactly one custom component.

## First installation

1. Back up your HA configuration.
2. Copy **only** `custom_components/apco_maniacs/` to `/config/custom_components/apco_maniacs/` and restart Home Assistant. Leave the existing `warun` integration and unrelated configuration files in place.
3. Open **Settings → Devices & services → Add integration → APCO Maniacs**.
4. Enter a location name, choose its map pin, set its explicit IANA time zone and wind/precipitation thresholds. New entries start at the HA home coordinates. Settings are validated against Open-Meteo before saving. Each different location can have its own entry.
5. Install the matching preview card from this branch: copy `dist/apco-maniacs-card.js` to `/config/www/apco-maniacs-card/`, and use `/local/apco-maniacs-card/apco-maniacs-card.js?v=integration-preview` as the JavaScript module resource. If you already use the HACS resource, temporarily **replace its resource entry** rather than loading both builds. The stable 1.0.10 card does not read integration entities.
6. In the card's visual editor choose the **Conditions** entity under “APCO Maniacs integration entity”. Find the real entity ID on the integration's device page; the example below is not guaranteed to match your installation.

```yaml
type: custom:apco-maniacs-card
entity: sensor.apco_maniacs_piecki_conditions
# Optional: otherwise follows the HA frontend language.
language: en
daylight_only: true
forecast_hours: 40
```

Clear the entity in the card editor to return to direct browser forecasts. Existing cards without `entity` and the standalone page continue to work without the backend.

## Entities and configuration

Each entry creates one service device and four sensors:

| Sensor | Value |
| --- | --- |
| Conditions | `good`, `bad`, or `unknown`; displayed using HA translations |
| Temperature | Current temperature, native °C |
| Wind speed | Current wind, native m/s; HA can convert the display unit |
| Precipitation probability | Probability for the current forecast hour, % |

The conditions entity carries `apco_maniacs: true`, `forecast`, `updated_at` (UTC epoch seconds), and `location` (name, latitude, longitude, IANA time zone and both thresholds). `forecast` uses the Open-Meteo structure, UTC epoch seconds, m/s and °C, and contains at most five days. Only this sensor carries the forecast, and it is excluded from Recorder attributes to avoid storing it on every update. Numeric sensors can be used in automations and history. Enum state values remain stable across languages; the new integration's PL/EN/IT/ES display translations follow HA. The older Warun sensor retains its separate PL/EN language option.

The current assessment combines **current wind** with the **current hour's precipitation probability**. Both must be strictly below their thresholds. Missing, invalid or stale values never produce `good`. On a fetch failure the sensors become unavailable; previous card intervals may remain visible with an error and the current verdict paused. There is no silent switch to a browser fetch. A successful update restores availability. The card refresh button calls HA's `homeassistant.update_entity`; automatic polling is shared among all cards for the same entry.

Use the integration's **Configure** action to change its name, map pin, time zone or thresholds. These override the card's old location/threshold settings while an entity is selected. The card still controls language, forecast horizon and daylight filtering. Changing a pin or name keeps the entry and entity IDs. Duplicate location/time zone entries are rejected. Changing this integration does not alter the HA home location, other entries or the legacy `warun` integration.

Forecast intervals keep the existing card rules: start at the current full hour, merge adjacent equal assessments without a three-hour limit, split at gaps/local midnight/verdict changes, clip at sunset including minutes, and restart the next day at the first full hour at or after sunrise. Today's windows disappear once sunset has passed, with the existing explanation on the next date heading.

## Updating and removing the preview

For updates, replace only the `apco_maniacs` component folder and the preview card file, restart HA, change the resource cache suffix, then fully refresh the dashboard. Existing entries and entities remain. Do not overwrite `configuration.yaml`, automations, scripts or scenes.

To roll back, clear `entity` from the card and restore the stable HACS resource. Remove the integration entries in Devices & services before deleting the optional component folder and restarting HA. Cards without an integration entity continue to fetch their own weather.

## Icon and distribution

The independent project icon combines a blue paraglider canopy with the sun. `brand/icon.png` (256 px) and `brand/icon@2x.png` (512 px) are included for Home Assistant's local brand API, introduced in 2026.3. Matching `dark_icon` variants keep the lines visible on dark themes. The SVGs are the editable masters. An icon in Devices & services does not itself publish a HACS listing. Discovery/list icons also depend on the HACS/Marketplace version, its catalogue and caches; do not promise immediate visibility before publishing an integration repository.

From the card source repository:

```sh
python3 scripts/package_integration.py
```

This produces `output/apco-maniacs-integration.zip`, containing the installable `custom_components/apco_maniacs/` tree, and `output/apco-maniacs-integration/`, an isolated repository layout with one component, its own `hacs.json`, this guide and the MIT license. The exporter never writes into the live HA configuration. Publishing it as a separate repository and adding a HACS catalogue submission are separate steps; the exporter does neither. No changes to the existing card listing are required.

## Verification

```sh
npm test
npm run check:dist
python3 -m unittest discover -s tests
# In a separate Python 3.14 environment with homeassistant==2026.3.0 or 2026.11.1 installed:
python -m unittest discover -s integration_tests
```

The runtime tests run real HA config flows, entity registration, option reloads, unloads and recovery with the HTTP session mocked. They do not test the native map visually or a user's installed HACS interface.

Weather: [Open-Meteo](https://open-meteo.com/), [CC BY 4.0](https://open-meteo.com/en/terms). Coordinates are sent to Open-Meteo by the HA server. The public API is for non-commercial use; commercial deployments need the appropriate provider terms. Independent community project, not an official APCO Aviation product. The weather assessment does not account for turbulence, gusts, thermals or terrain and is not a flight safety guarantee.

[Support the project](https://buymeacoffee.com/piotrwoznil) · [Piotrek Lata on YouTube](https://www.youtube.com/@piter_fly)
