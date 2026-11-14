"""Backend contract tests; runnable with the repository's standard unittest command."""
import copy
import json
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[1]
DATA = runpy.run_path(str(ROOT / 'custom_components/apco_maniacs/data.py'))
DEFAULTS = runpy.run_path(str(ROOT / 'custom_components/apco_maniacs/const.py'))['DEFAULTS']
FIXTURE = json.loads((ROOT / 'tests/fixtures/open_meteo.json').read_text())
NOW = FIXTURE['current']['time']


class ForecastTests(unittest.TestCase):
    def test_valid_forecast_keeps_wire_contract_without_mutating_source(self):
        before = copy.deepcopy(FIXTURE)
        clean = DATA['validate_forecast'](FIXTURE, NOW)
        self.assertEqual(FIXTURE, before)
        self.assertEqual(clean['hourly'], FIXTURE['hourly'])
        self.assertEqual(DATA['current_values'](clean, NOW), {'temperature': 10, 'wind': 3.2, 'precipitation': 0})
        self.assertEqual(DATA['assessment'](DATA['current_values'](clean, NOW), DEFAULTS), 'good')

    def test_current_hour_is_selected_by_timestamp_not_first_forecast_row(self):
        raw = copy.deepcopy(FIXTURE)
        raw['hourly']['precipitation_probability'][0] = 90
        raw['current']['time'] = NOW + 3600
        clean = DATA['validate_forecast'](raw, NOW + 3600)
        self.assertEqual(DATA['current_values'](clean, NOW + 3600)['precipitation'], 0)

    def test_thresholds_and_missing_or_invalid_numbers(self):
        for wind, precip, expected in [(4.99, 9.99, 'good'), (5, 0, 'bad'), (0, 10, 'bad'),
                                      (None, 0, 'unknown'), (0, None, 'unknown'),
                                      (-1, 0, 'unknown'), (0, 101, 'unknown'), (True, 0, 'unknown'),
                                      (float('nan'), 0, 'unknown')]:
            with self.subTest(wind=wind, precip=precip):
                raw = copy.deepcopy(FIXTURE)
                raw['current']['wind_speed_10m'] = wind
                raw['hourly']['precipitation_probability'][0] = precip
                clean = DATA['validate_forecast'](raw, NOW)
                values = DATA['current_values'](clean, NOW)
                self.assertEqual(DATA['assessment'](values, DEFAULTS), expected)

    def test_stale_data_wrong_units_and_malformed_arrays_fail(self):
        for mutate in [lambda p: p['hourly_units'].update(wind_speed_10m='km/h'),
                       lambda p: p['current_units'].update(temperature_2m='°F'),
                       lambda p: p['current'].update(time=NOW-3600),
                       lambda p: p['hourly'].update(time=[]),
                       lambda p: p['hourly'].update(time=[NOW+3600]),
                       lambda p: p['hourly'].update(wind_speed_10m=[]),
                       lambda p: p['daily'].update(sunset=[]),
                       lambda p: p['hourly']['time'].__setitem__(1, NOW-1000)]:
            raw = copy.deepcopy(FIXTURE)
            mutate(raw)
            with self.assertRaises(ValueError):
                DATA['validate_forecast'](raw, NOW)

    def test_future_and_stale_current_values_do_not_assess_good(self):
        clean = DATA['validate_forecast'](FIXTURE, NOW)
        for now in (NOW-1, NOW+3600):
            self.assertEqual(DATA['assessment'](DATA['current_values'](clean, now), DEFAULTS), 'unknown')

    def test_settings_validate_coordinates_thresholds_and_timezone(self):
        for key, value in [('latitude', 91), ('longitude', float('inf')), ('name', ' '),
                           ('wind_threshold', 0), ('precip_threshold', 101), ('timezone', '../UTC')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                DATA['validate_settings']({**DEFAULTS, key: value})
        self.assertEqual(DATA['validate_settings']({**DEFAULTS, 'name':' Piecki '})['name'], 'Piecki')
        params = DATA['forecast_params'](DEFAULTS)
        self.assertEqual((params['wind_speed_unit'], params['timeformat'], params['forecast_days']), ('ms', 'unixtime', 5))

    def test_translations_have_same_structure_and_forecast_is_not_recorded(self):
        def keys(value):
            return {k: keys(v) if isinstance(v, dict) else None for k, v in value.items()}
        folder = ROOT/'custom_components/apco_maniacs'
        expected = json.loads((folder/'strings.json').read_text())
        for lang in ('pl', 'en', 'it', 'es'):
            self.assertEqual(keys(json.loads((folder/f'translations/{lang}.json').read_text())), keys(expected))

    def test_export_contains_one_component_and_installable_brand_assets(self):
        import struct
        import tempfile
        from zipfile import ZipFile
        package = runpy.run_path(str(ROOT/'scripts/package_integration.py'))['package']
        with tempfile.TemporaryDirectory() as temp:
            target, archive = package(temp)
            self.assertEqual([p.name for p in (target/'custom_components').iterdir()], ['apco_maniacs'])
            self.assertEqual(json.loads((target/'hacs.json').read_text())['homeassistant'], '2026.3.0')
            with ZipFile(archive) as bundle:
                names = bundle.namelist()
                self.assertIn('custom_components/apco_maniacs/config_flow.py', names)
                self.assertEqual(bundle.read('custom_components/apco_maniacs/frontend/apco-weather-card.js'),
                                 (ROOT/'dist/apco-maniacs-card.js').read_bytes())
                self.assertFalse(any('__pycache__' in n or n.endswith('.pyc') for n in names))
                for suffix, size in [('', 256), ('@2x', 512)]:
                    png = bundle.read(f'custom_components/apco_maniacs/brand/icon{suffix}.png')
                    self.assertEqual(struct.unpack('>II', png[16:24]), (size, size))
