"""Serve the bundled dashboard card from the integration package."""
from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.loader import async_get_integration

from .const import DOMAIN

CARD_PATH = "/apco-weather/apco-weather-card.js"


async def async_register_card(hass):
    """HA loads the bundled module automatically, including for YAML dashboards."""
    integration = await async_get_integration(hass, DOMAIN)
    path = Path(__file__).parent / "frontend" / "apco-weather-card.js"
    await hass.http.async_register_static_paths([
        StaticPathConfig(CARD_PATH, str(path), cache_headers=False),
    ])
    frontend.add_extra_js_url(hass, f"{CARD_PATH}?v={integration.version}")
