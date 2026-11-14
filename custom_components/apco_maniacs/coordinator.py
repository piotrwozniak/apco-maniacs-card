"""One Open-Meteo request per location, shared by all entities and cards."""
from asyncio import timeout
from datetime import timedelta
import logging

from aiohttp import ClientError, ClientSession
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import API_URL, DOMAIN
from .data import forecast_params, validate_forecast, validate_settings

_LOGGER = logging.getLogger(__name__)


async def async_fetch_forecast(session: ClientSession, settings):
    """Request a bounded five-day forecast; a failed request never counts as an update."""
    async with timeout(20):
        async with session.get(API_URL, params=forecast_params(settings)) as response:
            response.raise_for_status()
            payload = await response.json()
    return validate_forecast(payload, dt_util.utcnow().timestamp())


class APCOCoordinator(DataUpdateCoordinator):
    """Poll Open-Meteo every fifteen minutes, including without an open dashboard."""

    def __init__(self, hass, entry):
        super().__init__(hass, _LOGGER, name=DOMAIN, config_entry=entry,
                         update_interval=timedelta(minutes=15))
        self.settings = validate_settings({**entry.data, **entry.options})
        self.updated_at = None

    async def _async_update_data(self):
        try:
            forecast = await async_fetch_forecast(async_get_clientsession(self.hass), self.settings)
        except (ClientError, TimeoutError, ValueError, TypeError) as err:
            raise UpdateFailed(f"Open-Meteo: {err}") from err
        self.updated_at = dt_util.utcnow().timestamp()
        return forecast
