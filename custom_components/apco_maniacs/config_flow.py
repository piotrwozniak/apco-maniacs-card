"""Configure a named location on HA's native map; no weather entity or API key needed."""
from aiohttp import ClientError
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import LocationSelector

from .const import DEFAULTS, DOMAIN
from .coordinator import async_fetch_forecast
from .data import validate_settings


def schema(settings):
    return vol.Schema({
        vol.Required("name", default=settings["name"]): str,
        vol.Required("location", default={key: settings[key] for key in ("latitude", "longitude")}): LocationSelector(),
        vol.Required("timezone", default=settings["timezone"]): str,
        vol.Required("wind_threshold", default=settings["wind_threshold"]): vol.All(vol.Coerce(float), vol.Range(min=0.5, max=30)),
        vol.Required("precip_threshold", default=settings["precip_threshold"]): vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
    })


async def validate_input(hass, user_input):
    location = user_input.get("location", {})
    settings = validate_settings({**user_input, "latitude": location.get("latitude"), "longitude": location.get("longitude")})
    settings.pop("location", None)
    await async_fetch_forecast(async_get_clientsession(hass), settings)
    return settings


def duplicate_location(hass, settings, entry_id=None):
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.entry_id == entry_id:
            continue
        other = {**entry.data, **entry.options}
        if all(other.get(key) == settings[key] for key in ("latitude", "longitude", "timezone")):
            return True
    return False


class APCOConfigFlow(ConfigFlow, domain=DOMAIN):
    """Create independent entries for multiple launch sites."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        settings = {**DEFAULTS, "latitude": self.hass.config.latitude, "longitude": self.hass.config.longitude,
                    "timezone": self.hass.config.time_zone}
        errors = {}
        if user_input is not None:
            try:
                settings = await validate_input(self.hass, user_input)
            except (ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            except (ValueError, TypeError):
                errors["base"] = "invalid_data"
            else:
                if duplicate_location(self.hass, settings):
                    return self.async_abort(reason="already_configured")
                return self.async_create_entry(title=settings["name"], data=settings)
        return self.async_show_form(step_id="user", data_schema=self.add_suggested_values_to_schema(schema(settings), user_input), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return APCOOptionsFlow()


class APCOOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input=None):
        settings = {**self.config_entry.data, **self.config_entry.options}
        errors = {}
        if user_input is not None:
            try:
                new_settings = await validate_input(self.hass, user_input)
            except (ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            except (ValueError, TypeError):
                errors["base"] = "invalid_data"
            else:
                if duplicate_location(self.hass, new_settings, self.config_entry.entry_id):
                    errors["base"] = "already_configured"
                else:
                    self.hass.config_entries.async_update_entry(self.config_entry, title=new_settings["name"])
                    return self.async_create_entry(title="", data=new_settings)
        return self.async_show_form(step_id="init", data_schema=self.add_suggested_values_to_schema(schema(settings), user_input), errors=errors)
