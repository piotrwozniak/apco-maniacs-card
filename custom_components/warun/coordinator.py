"""Coordinator for Warun integration – fetches hourly forecast via weather.get_forecasts."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=15)


class WarunCoordinator(DataUpdateCoordinator[list[dict[str, Any]] | None]):
    """Coordinator that fetches hourly forecast via weather.get_forecasts service."""

    def __init__(self, hass: HomeAssistant, weather_entity: str) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"warun_{weather_entity}",
            update_interval=SCAN_INTERVAL,
        )
        self._weather_entity = weather_entity
        self._unsub: callable | None = None

    async def _async_setup(self) -> None:
        """Set up the state change listener."""
        self._unsub = async_track_state_change_event(
            self.hass,
            [self._weather_entity],
            self._on_state_change,
        )

    @callback
    def _on_state_change(self, event) -> None:
        """Handle weather entity state change – trigger forecast re-fetch."""
        _LOGGER.debug(
            "Weather entity %s changed, requesting forecast refresh",
            self._weather_entity,
        )
        self.async_request_refresh()

    async def _async_update_data(self) -> list[dict[str, Any]] | None:
        """Fetch hourly forecast via weather.get_forecasts service."""
        try:
            response = await self.hass.services.async_call(
                "weather",
                "get_forecasts",
                {"type": "hourly"},
                blocking=True,
                target={"entity_id": self._weather_entity},
                return_response=True,
            )
        except Exception as err:
            raise UpdateFailed(
                f"Failed to fetch forecast for {self._weather_entity}: {err}"
            ) from err

        entity_response = response.get(self._weather_entity)
        if entity_response is None:
            raise UpdateFailed(
                f"No forecast data returned for {self._weather_entity}"
            )

        forecast: list[dict[str, Any]] | None = entity_response.get("forecast")
        if not forecast:
            _LOGGER.warning(
                "Empty hourly forecast for %s. Check API subscription/limits.",
                self._weather_entity,
            )

        return forecast

    async def async_config_entry_first_refresh(self) -> None:
        """Perform first refresh and set up listener."""
        await self._async_setup()
        await super().async_config_entry_first_refresh()

    async def async_shutdown(self) -> None:
        """Clean up."""
        if self._unsub:
            self._unsub()
            self._unsub = None
        await super().async_shutdown()
