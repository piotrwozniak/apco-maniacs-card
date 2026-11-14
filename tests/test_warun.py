"""Checks without requiring a Home Assistant installation."""
import ast
import runpy
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
source = ast.parse((ROOT / 'legacy/custom_components/warun/sensor.py').read_text())
selected = [node for node in source.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))]
namespace = {
    'CoordinatorEntity': type('CoordinatorEntity', (), {}),
    'SensorEntity': type('SensorEntity', (), {}),
    'SENSOR_DESCRIPTION': None,
    'callback': lambda fn: fn,
    'WIND_DIRECTIONS': ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                        'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'],
}
namespace.update(runpy.run_path(str(ROOT / 'legacy/custom_components/warun/const.py')))
module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), *selected], type_ignores=[])
exec(compile(ast.fix_missing_locations(module), 'sensor.py', 'exec'), namespace)


class WarunTests(unittest.TestCase):
    def sensor(self, wind=10.8, precip=5):
        sensor = namespace['WarunSensor'].__new__(namespace['WarunSensor'])
        sensor._language = "pl"
        sensor._weather_entity = 'weather.test'
        sensor._wind_threshold = 5
        sensor._precip_threshold = 10
        sensor._forecast_hours = 40
        sensor._latitude = sensor._longitude = None
        state = SimpleNamespace(attributes={'wind_speed_unit': 'km/h'})
        sensor.hass = SimpleNamespace(states=SimpleNamespace(get=lambda _: state))
        sensor.coordinator = SimpleNamespace(data=[{
            'wind_speed': wind, 'precipitation_probability': precip,
            'datetime': None,
        }] * 40)
        sensor.async_write_ha_state = lambda: None
        return sensor

    def test_short_state_and_full_description(self):
        sensor = self.sensor()
        sensor._handle_coordinator_update()
        self.assertEqual(sensor._attr_native_value, 'Warun')
        self.assertLessEqual(len(sensor._attr_native_value), 255)
        self.assertGreater(len(sensor.extra_state_attributes['opis']), 255)

    def test_normalized_forecast_does_not_mutate_source(self):
        sensor = self.sensor()
        sensor._handle_coordinator_update()
        self.assertAlmostEqual(sensor.extra_state_attributes['forecast_raw'][0]['wind_speed'], 3)
        self.assertEqual(sensor.coordinator.data[0]['wind_speed'], 10.8)

    def test_missing_data_is_not_good_weather(self):
        for wind, precip in [(None, 5), (10.8, None)]:
            sensor = self.sensor(wind, precip)
            sensor._handle_coordinator_update()
            self.assertEqual(sensor._attr_native_value, 'Brak danych')

    def test_threshold_is_exclusive(self):
        sensor = self.sensor(18, 5)
        sensor._handle_coordinator_update()
        self.assertEqual(sensor._attr_native_value, 'Brak warunu')


    def test_english_sensor_state_and_description(self):
        sensor = self.sensor()
        sensor._language = "en"
        sensor._handle_coordinator_update()
        self.assertEqual(sensor._attr_native_value, 'Flyable')
        self.assertIn('Now:', sensor.extra_state_attributes['opis'])
        self.assertNotIn('Teraz', sensor.extra_state_attributes['opis'])
        self.assertEqual(sensor.extra_state_attributes['language'], 'en')


if __name__ == '__main__':
    unittest.main()
