# Project Guidelines

Home Assistant YAML configuration for weather monitoring and waste collection reminders in Warmia-Mazury, Poland.

## Language

Default user-facing strings are in **Polish**. APCO Maniacs weather UI and sensor descriptions support explicitly selected **Polish, English, Italian or Spanish** (`language: pl` / `en` / `it` / `es`) in the web card; Python sensor output separately supports Polish or English; translate all weather UI strings, dates and number formats. Automation aliases, notifications and trash categories remain Polish. Template comments and variable names may mix Polish and English. New additions should follow this convention.

## Architecture

Configuration is split via `!include` directives in `configuration.yaml`:

| Include | File | Status |
|---------|------|--------|
| `automation: !include automations.yaml` | `automations.yaml` | Active |
| `script: !include scripts.yaml` | `scripts.yaml` | Active |
| `scene: !include scenes.yaml` | `scenes.yaml` | Active — empty list |

Weather integrations (`weather.forecast_dom`, `weather.piecki`, `weather.faryny`) are configured outside these files (likely via UI). The `met.no` REST sensors in `configuration.yaml` (lines 4–29) are fully commented out and should not be reactivated.

## Custom Components

### Warun (`custom_components/warun/`)

A HACS-compatible integration that replaces the template-based `sensor.warun_faryny`. Provides a sensor platform for weather conditions assessment.

- **Installation**: copy `custom_components/warun/` to HA's `custom_components/` dir, or add this repo to HACS
- **Config**: via UI (Settings → Devices & Services → Add Integration → Warun) — select a weather entity
- **Options**: wind threshold (m/s), precipitation threshold (%), forecast hours count
- **Architecture**: uses `DataUpdateCoordinator` + state change listeners on the weather entity. Fetches hourly forecast via `weather.get_forecasts` service (type=hourly) — no longer relies on the deprecated `state.attributes.forecast`. Current weather conditions (temp, wind, humidity) are read from the weather entity's state attributes, which remain available.
- **Files**: `__init__.py` (entry setup), `sensor.py` (sensor logic + state builder), `coordinator.py` (entity tracking), `config_flow.py` (UI config), `const.py`, `manifest.json`, `strings.json`, `hacs.json`

## Template Sensors

### Trash Schedule (`sensor.trashes_today`)

Two hardcoded arrays of `{'date': 'YYYY-MM-DD', 'trash': 'category'}` objects — one for house (`dom`), one for company (`firma`). Filtered by today's date with:

```yaml
trashes_house | selectattr('date', 'eq', today) | map(attribute='trash') | join(', ')
```

Trash categories use shorthand variables defined at the top of the template. The output conditionally formats based on which entity has pickups today.

### Weather Conditions (`sensor.warun_faryny`) — **superseded by custom component**

Removed from configuration.yaml; use the custom integration. The former sensor used a reusable nested macro pattern — `checkWarun(sensorName)` contains inner macros for wind direction conversion, current weather info, and per-hour forecast formatting.

Each forecast hour is classified **OK** (wind < 5 m/s AND precipitation < 10%) or **NOT OK**.

Iterates over 40 hours of hourly forecast via `{% for i in range(0, 40) %}`.

This sensor should be replaced by the **Warun** integration (`custom_components/warun/`) which provides the same functionality via UI configuration and fetches hourly forecast via the `weather.get_forecasts` service.

## Markdown Cards

### `md_card_place` — Warun do latania, okna 3-godzinne

Lovelace Markdown card template in `custom_components/md_card_place/md_card_place`. Displays a 3-hour-window flying-conditions assessment with color-coded `<ha-alert>` blocks.

- **Data source**: reads `forecast_raw` attribute from a `sensor.warun_*` entity (requires the Warun custom component)
- **Config**: `sensor_name` (warun sensor), `wind_threshold` (m/s), `precip_threshold` (%), `wind_convert` (1.0 — data already in m/s)
- Uses sunrise/sunset from `sun.sun` to hide windows outside flying hours

### Entity ID Patterns

- Weather: `weather.<location_or_purpose>` — `weather.piecki`, `weather.faryny`, `weather.forecast_dom`
- Sensors: `sensor.<location>_<metric>` — `sensor.faryny_temperature`, `sensor.faryny_cloud_coverage`
- Dynamic references construct entity IDs via string concatenation: `states('sensor.' + sensor_name + '_temperature')`

## Automations

- All use `mode: single` to prevent concurrent runs
- IDs are Unix timestamps
- Triggers are time-based only (`platform: time`)
- Conditions use Jinja2 template expressions
- Notifications target `notify.mobile_app_gutek` and `notify.notify` (with `mobile_app_iphone_m` as additional target)

## Scripts

- Script keys in `snake_case` English (`get_forecast_for_piecki`)
- Uses `response_variable` pattern (HA 2023.6+) for chained action responses

## No Build/Test Commands

This is a Home Assistant configuration repo. Validate YAML syntax manually or deploy to a HA instance for testing. Lightweight regression checks: `python3 -m unittest discover -s tests`. These do not replace validation on a running HA instance.

## Deployment documentation

Keep `wdrozenie.html` (Polish step-by-step deployment guide) up to date whenever changes affect installation, deployment files, configuration, entity IDs, sensor attributes, schedules, or post-update actions. Update the guide in the same change, including its displayed update date when its content changes. Preserve the distinction between first installation and an update; never instruct users to overwrite unrelated live configuration or existing scenes.

## Standalone web component

`warun-web/` implements the weather/flying assessment independently of Home Assistant, using Open-Meteo directly. `warun-card.js` registers the same `<warun-card>` Web Component for standalone `index.html` and HA `type: custom:warun-card`; do not add a simulated HA interface. `weather.mjs` contains normalization and assessment/window logic, `warun.css` contains Shadow DOM styles. No runtime packages or build step for standalone sources. For HACS, run `npm run build` to regenerate the committed single-file `dist/apco-maniacs-card.js`; `npm run check:dist` verifies it matches the sources. HACS installs this repository as Dashboard/plugin, not as a Python integration. The product name is **APCO Maniacs**; the canonical web element and HA card type are `apco-maniacs-card` / `custom:apco-maniacs-card`, with `warun-card` retained for compatibility. Use Home Assistant theme variables with dark standalone fallbacks and a small paragliding canopy in the header; preserve the simple forecast layout. `i18n.mjs` contains PL/EN/IT/ES dictionaries. The native HA card editor saves language and location settings to card configuration; integration Python has an independent language option for sensor output. Tests: `node --test warun-web/*.test.mjs`. Deployment instructions for both standalone and HA use are in `wdrozenie.html`. Copy all four runtime files (`warun-card.js`, `weather.mjs`, `i18n.mjs`, `warun.css`) together when deploying to HA's `www/warun-web/`.

The web component should preserve the original Markdown card presentation: colored alert blocks for current conditions and forecast intervals grouped by hourly assessment, with time range, temperature range | max wind with only a source-direction abbreviation (e.g. WNW), without arrows | max precipitation. Preserve the simple pipe-separated layout; do not add a compass or oversized wind figures. Color conveys the verdict: do not add check marks, passing-hours counts, repeated verdict labels or expandable hourly details. Keep the daylight filter; explain when it hides all remaining windows today. Do not replace intervals with an hourly bar chart.

Web forecast windows start at the current full hour (14:15 → 14:00). Assess each hour, then merge contiguous hours with the same assessment without a three-hour limit. Split on assessment changes, missing forecast timestamps, local calendar day boundaries, or sunset when daylight-only is enabled. Clip to sunset, including its minute (e.g. 17:24), using hourly weather data. Each following day restarts at the first full hour at or after sunrise (09:20 → 10:00); do not use sunrise minus one hour or carry the previous day’s phase. Preserve these rules in regression tests and deployment docs. Show prominent capitalized date headings without a separate forecast/daylight heading. The compact header shows the location, the localized APCO weather subtitle, and a small borderless refresh icon in the location row. Wind direction abbreviations are bold.

## HACS publication and editor

Root `hacs.json` selects `dist/apco-maniacs-card.js`. The dependency-free packaging script embeds CSS, translations and image in one JS file. Keep it in sync after source edits. The native HA card editor loads `ha-form` through the native entities card editor and uses HA's location selector; do not add a simulated HA UI or external map library. Pin changes persist latitude/longitude and retain the other card settings. New cards start at the HA home coordinates. Time zone remains an explicit setting.

Support links in `warun-web/i18n.mjs` point to `https://buymeacoffee.com/piotrwoznil` and `https://www.youtube.com/@piter_fly`; mirror these in README, deployment docs and `.github/FUNDING.yml` as applicable. Publication workflows validate HACS category `plugin` and attach the single JS asset on a published GitHub release.

Web card language follows the HA frontend when `language` is omitted. Supported regional language tags normalize to PL/EN/IT/ES; all unmatched languages fall back to English. An explicit supported language overrides HA. Keep all four dictionaries complete and README.md (English default) / README.pl.md / README.it.md / README.es.md aligned. Native HA map controls use HA’s own localization.

The default README and HACS listing description are English. README.en.md is a compatibility link to README.md. Documentation screenshots use the real standalone component in English for Warsaw and Piecki. The Warsaw screenshot fixture is explicitly simulated and isolated in warun-web/demo-warsaw.json; never include demo forecasts in the production card or HACS bundle.
