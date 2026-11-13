"""Sensor platform for weather conditions (warun) assessment."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    CONF_FORECAST_HOURS,
    CONF_LANGUAGE,
    DEFAULT_LANGUAGE,
    DEFAULT_NAME,
    TEXT,
    CONF_LATITUDE,
    CONF_LOCATION_NAME,
    CONF_LONGITUDE,
    CONF_PRECIP_THRESHOLD,
    CONF_WEATHER_ENTITY,
    CONF_WIND_THRESHOLD,
    DOMAIN,
    WIND_DIRECTIONS,
)
from .coordinator import WarunCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTION = SensorEntityDescription(
    key="warun",
    icon="mdi:weather-windy",
    has_entity_name=True,
)


def _convert_wind_direction(degrees: float | None) -> str:
    """Convert wind bearing in degrees to 16-point compass direction."""
    if degrees is None:
        return "?"

    # 16 directions, each 22.5°, offset by 11.25° for centering
    idx = int((degrees + 11.25) / 22.5) % 16
    return WIND_DIRECTIONS[idx]


def _to_mps(value: float | None, unit: str | None) -> float:
    """Convert wind speed to m/s based on unit."""
    if value is None:
        return 0.0
    if unit and unit.startswith("km"):
        return value / 3.6
    return value * {"mph": 0.44704, "kn": 0.514444, "ft/s": 0.3048}.get(unit, 1.0)


def _build_state(
    weather_state,
    forecast: list[dict] | None,
    wind_threshold: float,
    precip_threshold: float,
    forecast_hours: int,
    language: str = "pl",
) -> str:
    """Build the warun sensor state text from weather and forecast data."""
    text = TEXT[language]
    lines: list[str] = []

    # Current conditions
    attrs = weather_state.attributes
    temp = attrs.get("temperature")
    humidity = attrs.get("humidity")
    wind_speed = attrs.get("wind_speed")
    wind_bearing = attrs.get("wind_bearing")
    wind_unit = attrs.get("wind_speed_unit", "m/s")
    pressure = attrs.get("pressure")
    precip = attrs.get("precipitation_probability")

    temp_str = f"{temp:.0f}°C" if temp is not None else "?"
    cloud = attrs.get("cloud_coverage", "?")
    cloud_str = f"{cloud}%"

    lines.append(f"{text['now']}: {temp_str}, {text['cloud']} {cloud_str}")

    wind_ms = _to_mps(wind_speed, wind_unit)
    wind_dir = _convert_wind_direction(wind_bearing)
    lines.append(f"{text['wind']}: {wind_ms:.1f} m/s {wind_dir}")

    if humidity is not None:
        lines.append(f"{text['humidity']}: {humidity}%")
    if pressure is not None:
        lines.append(f"{text['pressure']}: {pressure} hPa")
    if precip is not None:
        lines.append(text["no_rain"] if precip == 0 else f"{text['rain']}: {precip:.0f}%")

    # Forecast hours
    if forecast:
        lines.append("")
        limit = min(len(forecast), forecast_hours)
        for i in range(limit):
            f = forecast[i]
            f_temp = f.get("temperature")
            f_wind_raw = f.get("wind_speed")
            f_wind_bearing = f.get("wind_bearing")
            f_precip = f.get("precipitation_probability")

            f_wind = _to_mps(f_wind_raw, wind_unit)

            f_dt = f.get("datetime")
            try:
                if isinstance(f_dt, str):
                    f_dt_parsed = dt_util.parse_datetime(f_dt)
                    local_dt = dt_util.as_local(f_dt_parsed) if f_dt_parsed else None
                    time_str = f"{text['days'][local_dt.weekday()]} {local_dt:%H:%M}" if local_dt else "?"
                else:
                    time_str = f"{text['days'][f_dt.weekday()]} {f_dt:%H:%M}" if f_dt else "?"
            except (ValueError, AttributeError):
                time_str = "?"

            temp_part = f"{f_temp:.0f}°C" if f_temp is not None else "?"
            wind_part = f"{f_wind:.1f} m/s {_convert_wind_direction(f_wind_bearing)}"
            precip_part = f"{f_precip:.0f}%" if f_precip is not None else "?"

            is_ok = f_wind_raw is not None and f_precip is not None and f_wind < wind_threshold and f_precip < precip_threshold
            status = text["yes"] if is_ok else text["no"]

            lines.append(
                f"{time_str} ({status}): {temp_part}, {text['wind']} {wind_part}, "
                + (text["no_rain"] if f_precip == 0 else f"{text['rain']} {precip_part}")
            )
    else:
        lines.append("")
        lines.append(text["no_forecast"])

    return "\n".join(lines)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Warun sensor from a config entry."""
    weather_entity: str = entry.data[CONF_WEATHER_ENTITY]
    name: str = entry.data.get(CONF_LOCATION_NAME, entry.data.get(CONF_NAME, DEFAULT_NAME))
    latitude: float | None = entry.data.get(CONF_LATITUDE)
    longitude: float | None = entry.data.get(CONF_LONGITUDE)
    wind_threshold: float = entry.options.get(
        CONF_WIND_THRESHOLD, entry.data.get(CONF_WIND_THRESHOLD, 5.0)
    )
    precip_threshold: float = entry.options.get(
        CONF_PRECIP_THRESHOLD, entry.data.get(CONF_PRECIP_THRESHOLD, 10)
    )
    forecast_hours: int = entry.options.get(
        CONF_FORECAST_HOURS, entry.data.get(CONF_FORECAST_HOURS, 40)
    )

    coordinator = WarunCoordinator(hass, weather_entity)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [
            WarunSensor(
                coordinator=coordinator,
                entry=entry,
                name=name,
                latitude=latitude,
                longitude=longitude,
                wind_threshold=wind_threshold,
                precip_threshold=precip_threshold,
                forecast_hours=forecast_hours,
            )
        ]
    )


class WarunSensor(CoordinatorEntity, SensorEntity):
    """Sensor displaying weather conditions assessment."""

    entity_description = SENSOR_DESCRIPTION

    def __init__(
        self,
        coordinator: WarunCoordinator,
        entry: ConfigEntry,
        name: str,
        latitude: float | None,
        longitude: float | None,
        wind_threshold: float,
        precip_threshold: float,
        forecast_hours: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_warun"
        self._attr_name = name
        self._entry = entry
        self._weather_entity = entry.data[CONF_WEATHER_ENTITY]
        self._latitude = latitude
        self._longitude = longitude
        self._wind_threshold = wind_threshold
        self._precip_threshold = precip_threshold
        self._forecast_hours = int(forecast_hours)
        self._description = ""
        self._language = entry.options.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        attrs: dict[str, Any] = {
            "language": self._language,
            "weather_entity": self._weather_entity,
            "wind_threshold": self._wind_threshold,
            "precip_threshold": self._precip_threshold,
            "forecast_hours": self._forecast_hours,
        }
        if self._latitude is not None:
            attrs["latitude"] = self._latitude
        if self._longitude is not None:
            attrs["longitude"] = self._longitude

        # Expose raw forecast data so Markdown cards / templates can consume it
        forecast = self.coordinator.data
        if forecast:
            weather_state = self.hass.states.get(self._weather_entity)
            unit = weather_state.attributes.get("wind_speed_unit", "m/s") if weather_state else "m/s"
            attrs["forecast_raw"] = [
                {**hour, "wind_speed": _to_mps(hour.get("wind_speed"), unit)}
                for hour in forecast[:int(self._forecast_hours)]
            ]
        attrs["wind_speed_unit"] = "m/s"
        attrs["opis"] = self._description

        return attrs

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        forecast = self.coordinator.data  # list[dict] from weather.get_forecasts

        # Read current weather conditions from the weather entity state
        weather_state = self.hass.states.get(self._weather_entity)
        if weather_state is None:
            self._attr_native_value = None
            self.async_write_ha_state()
            return

        self._description = _build_state(
            weather_state,
            forecast,
            self._wind_threshold,
            self._precip_threshold,
            self._forecast_hours,
            self._language,
        )
        if not forecast:
            self._attr_native_value = TEXT[self._language]["no_forecast"]
        else:
            hour = forecast[0]
            wind = hour.get("wind_speed")
            precip = hour.get("precipitation_probability")
            if wind is None or precip is None:
                self._attr_native_value = TEXT[self._language]["missing"]
            else:
                unit = weather_state.attributes.get("wind_speed_unit", "m/s")
                is_ok = _to_mps(wind, unit) < self._wind_threshold and precip < self._precip_threshold
                self._attr_native_value = TEXT[self._language]["good" if is_ok else "bad"]
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()
