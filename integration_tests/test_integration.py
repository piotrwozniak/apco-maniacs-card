"""Tests against a real Home Assistant runtime with only the network mocked."""
import copy
from datetime import datetime, UTC
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant import loader
from homeassistant.config_entries import ConfigEntries, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import frame, entity_registry, device_registry, area_registry, floor_registry, label_registry
from homeassistant.setup import async_setup_component

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT/'tests/fixtures/open_meteo.json').read_text())
NOW = datetime.fromtimestamp(FIXTURE['current']['time'], UTC)


class IntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.hass = HomeAssistant(self.directory.name)
        self.hass.config.latitude = 52.2
        self.hass.config.longitude = 21.0
        self.hass.config.time_zone = 'Europe/Warsaw'
        self.hass.config.skip_pip = True
        loader.async_setup(self.hass)
        frame.async_setup(self.hass)
        self.hass.config_entries = ConfigEntries(self.hass, {})
        await self.hass.config_entries.async_initialize()
        self.session = MagicMock()
        response = self.session.get.return_value.__aenter__.return_value
        response.raise_for_status = MagicMock()
        response.json = AsyncMock(return_value=copy.deepcopy(FIXTURE))
        self.network = patch('custom_components.apco_maniacs.coordinator.async_get_clientsession', return_value=self.session)
        self.flow_network = patch('custom_components.apco_maniacs.config_flow.async_get_clientsession', return_value=self.session)
        self.network.start()
        self.flow_network.start()
        self.fetch = self.session.get
        self.clock = patch('homeassistant.util.dt.utcnow', return_value=NOW)
        self.clock.start()
        if hasattr(device_registry, "async_setup"):
            device_registry.async_setup(self.hass)
        for registry in (floor_registry, area_registry, label_registry, device_registry, entity_registry):
            await registry.async_load(self.hass)
        await async_setup_component(self.hass, 'homeassistant', {})

    async def asyncTearDown(self):
        await self.hass.async_stop(force=True)
        await self.hass.async_block_till_done()
        self.clock.stop()
        self.network.stop()
        self.flow_network.stop()
        self.directory.cleanup()

    def input(self, name='Piecki', latitude=53.7, **kwargs):
        return dict(name=name, location=dict(latitude=latitude, longitude=21.0), timezone='Europe/Warsaw',
                    wind_threshold=5.0, precip_threshold=10.0, **kwargs)

    async def create_entry(self, **kwargs):
        flow = await self.hass.config_entries.flow.async_init('apco_maniacs', context={'source':'user'})
        self.assertEqual(flow['type'], 'form')
        result = await self.hass.config_entries.flow.async_configure(flow['flow_id'], self.input(**kwargs))
        self.assertEqual(result['type'], 'create_entry', result)
        await self.hass.async_block_till_done()
        self.assertEqual(result['result'].state, ConfigEntryState.LOADED)
        return result['result']

    async def test_setup_entities_backend_attributes_and_unload(self):
        entry = await self.create_entry()
        states = self.hass.states.async_all('sensor')
        self.assertEqual(len(states), 4)
        self.assertEqual(self.fetch.call_count, 2, "One validation request and one shared setup request")
        conditions = next(state for state in states if state.attributes.get('apco_maniacs'))
        self.assertEqual(conditions.state, 'good')
        self.assertEqual(conditions.attributes['forecast']['hourly'], FIXTURE['hourly'])
        self.assertEqual(conditions.attributes['location']['name'], 'Piecki')
        self.assertEqual(sorted(s.state for s in states), ['0', '10', '3.2', 'good'])
        coordinator = entry.runtime_data
        self.assertEqual(coordinator.update_interval.total_seconds(), 900)
        await self.hass.config_entries.async_unload(entry.entry_id)
        await self.hass.async_block_till_done()
        self.assertEqual(entry.state, ConfigEntryState.NOT_LOADED)
        self.assertFalse(coordinator._listeners)
        self.assertIsNone(coordinator._unsub_refresh)

    async def test_options_keep_entity_ids_and_apply_threshold_and_pin(self):
        entry = await self.create_entry()
        ids = {s.entity_id for s in self.hass.states.async_all('sensor')}
        flow = await self.hass.config_entries.options.async_init(entry.entry_id)
        changed = self.input(name='Nowe Piecki', latitude=54)
        changed['wind_threshold'] = 3
        result = await self.hass.config_entries.options.async_configure(flow['flow_id'], changed)
        self.assertEqual(result['type'], 'create_entry', result)
        await self.hass.async_block_till_done()
        self.assertEqual({s.entity_id for s in self.hass.states.async_all('sensor')}, ids)
        self.assertEqual(entry.runtime_data.settings['latitude'], 54)
        conditions = next(s for s in self.hass.states.async_all('sensor') if s.attributes.get('apco_maniacs'))
        self.assertEqual(conditions.state, 'bad')
        self.assertEqual(entry.title, 'Nowe Piecki')

    async def test_network_failure_marks_entities_unavailable_and_recovery_restores_them(self):
        from aiohttp import ClientConnectionError
        entry = await self.create_entry()
        self.fetch.side_effect = ClientConnectionError('offline')
        await entry.runtime_data.async_refresh()
        self.assertTrue(all(s.state == 'unavailable' for s in self.hass.states.async_all('sensor')))
        self.fetch.side_effect = None
        await entry.runtime_data.async_refresh()
        self.assertIn('good', [s.state for s in self.hass.states.async_all('sensor')])

    async def test_multiple_locations_and_duplicates(self):
        await self.create_entry()
        flow = await self.hass.config_entries.flow.async_init('apco_maniacs', context={'source':'user'})
        result = await self.hass.config_entries.flow.async_configure(flow['flow_id'], self.input())
        self.assertEqual((result['type'], result.get('reason')), ('abort','already_configured'))
        await self.create_entry(name='Faryny', latitude=53.5)
        self.assertEqual(len(self.hass.states.async_all('sensor')), 8)

    async def test_config_flow_reports_offline_and_invalid_timezone(self):
        from aiohttp import ClientConnectionError
        flow = await self.hass.config_entries.flow.async_init('apco_maniacs', context={'source':'user'})
        data = self.input()
        data['timezone'] = 'Invalid/Zone'
        result = await self.hass.config_entries.flow.async_configure(flow['flow_id'], data)
        self.assertEqual(result['errors']['base'], 'invalid_data')
        self.fetch.side_effect = ClientConnectionError('offline')
        result = await self.hass.config_entries.flow.async_configure(flow['flow_id'], self.input())
        self.assertEqual(result['errors']['base'], 'cannot_connect')

    async def test_invalid_forecast_marks_unavailable_without_replacing_last_good_data(self):
        entry = await self.create_entry()
        previous = entry.runtime_data.data
        response = self.session.get.return_value.__aenter__.return_value
        response.json.return_value = {"hourly_units": {"wind_speed_10m": "km/h"}}
        await entry.runtime_data.async_refresh()
        self.assertIs(entry.runtime_data.data, previous)
        self.assertTrue(all(s.state == 'unavailable' for s in self.hass.states.async_all('sensor')))

    async def test_changing_pin_checks_duplicates_against_current_options(self):
        entry = await self.create_entry()
        other = await self.create_entry(name='Faryny', latitude=53.5)
        flow = await self.hass.config_entries.options.async_init(entry.entry_id)
        result = await self.hass.config_entries.options.async_configure(flow['flow_id'], self.input(latitude=53.5))
        self.assertEqual(result['errors']['base'], 'already_configured')
        moved = self.input(latitude=54)
        result = await self.hass.config_entries.options.async_configure(flow['flow_id'], moved)
        self.assertEqual(result['type'], 'create_entry')
        await self.hass.async_block_till_done()
        await self.create_entry(name='Old location', latitude=53.7)
        self.assertEqual(len(self.hass.config_entries.async_entries('apco_maniacs')), 3)

    async def test_stale_backend_timestamp_cannot_keep_a_good_sensor_available(self):
        entry = await self.create_entry()
        entry.runtime_data.updated_at -= 1801
        entry.runtime_data.async_update_listeners()
        self.assertTrue(all(s.state == 'unavailable' for s in self.hass.states.async_all('sensor')))
