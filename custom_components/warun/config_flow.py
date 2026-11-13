"""Config flow for Warun integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    LocationSelector,
    LocationSelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    TextSelector,
    TextSelectorConfig,
)

from .const import (
    CONF_FORECAST_HOURS,
    CONF_LANGUAGE,
    DEFAULT_LANGUAGE,
    CONF_LATITUDE,
    CONF_LOCATION_NAME,
    CONF_LONGITUDE,
    CONF_PRECIP_THRESHOLD,
    CONF_WEATHER_ENTITY,
    CONF_WIND_THRESHOLD,
    DEFAULT_FORECAST_HOURS,
    DEFAULT_PRECIP_THRESHOLD,
    DEFAULT_WIND_THRESHOLD,
    DOMAIN,
)

WEATHER_DOMAIN = "weather"


class WarunConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Warun."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._location_data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step – pick location on map."""
        errors: dict[str, str] = {}

        if user_input is not None:
            location = user_input.get("location")
            location_name = user_input.get(CONF_LOCATION_NAME, "").strip()

            if location is None:
                errors["location"] = "location_required"
            elif not location_name:
                errors[CONF_LOCATION_NAME] = "name_required"
            else:
                self._location_data = {
                    CONF_LATITUDE: location["latitude"],
                    CONF_LONGITUDE: location["longitude"],
                    CONF_LOCATION_NAME: location_name,
                }
                return await self.async_step_pick_weather()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("location"): LocationSelector(
                        LocationSelectorConfig()
                    ),
                    vol.Required(CONF_LOCATION_NAME): TextSelector(
                        TextSelectorConfig()
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_pick_weather(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select weather entity for the chosen location."""
        errors: dict[str, str] = {}

        if user_input is not None:
            weather_entity = user_input[CONF_WEATHER_ENTITY]

            for entry in self._async_current_entries():
                if entry.data.get(CONF_WEATHER_ENTITY) == weather_entity:
                    return self.async_abort(reason="already_configured")

            return self.async_create_entry(
                title=self._location_data[CONF_LOCATION_NAME],
                data={
                    **self._location_data,
                    CONF_WEATHER_ENTITY: weather_entity,
                },
            )

        return self.async_show_form(
            step_id="pick_weather",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_WEATHER_ENTITY): EntitySelector(
                        EntitySelectorConfig(
                            domain=WEATHER_DOMAIN,
                            multiple=False,
                        )
                    ),
                }
            ),
            errors=errors,
            description_placeholders={
                "location_name": self._location_data.get(CONF_LOCATION_NAME, ""),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return WarunOptionsFlow(config_entry)


class WarunOptionsFlow(OptionsFlow):
    """Handle Warun options."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current_wind = self._entry.options.get(
            CONF_WIND_THRESHOLD,
            self._entry.data.get(CONF_WIND_THRESHOLD, DEFAULT_WIND_THRESHOLD),
        )
        current_precip = self._entry.options.get(
            CONF_PRECIP_THRESHOLD,
            self._entry.data.get(CONF_PRECIP_THRESHOLD, DEFAULT_PRECIP_THRESHOLD),
        )
        current_hours = self._entry.options.get(
            CONF_FORECAST_HOURS,
            self._entry.data.get(CONF_FORECAST_HOURS, DEFAULT_FORECAST_HOURS),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_LANGUAGE,
                        default=self._entry.options.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                    ): SelectSelector(SelectSelectorConfig(options=[
                        {"value": "pl", "label": "Polski"},
                        {"value": "en", "label": "English"},
                    ], mode="dropdown")),
                    vol.Optional(
                        CONF_WIND_THRESHOLD,
                        default=current_wind,
                    ): NumberSelector(
                        NumberSelectorConfig(min=0.5, max=30, step=0.5, unit_of_measurement="m/s")
                    ),
                    vol.Optional(
                        CONF_PRECIP_THRESHOLD,
                        default=current_precip,
                    ): NumberSelector(
                        NumberSelectorConfig(min=0, max=100, step=5, unit_of_measurement="%")
                    ),
                    vol.Optional(
                        CONF_FORECAST_HOURS,
                        default=current_hours,
                    ): NumberSelector(
                        NumberSelectorConfig(min=1, max=48, step=1)
                    ),
                }
            ),
        )
