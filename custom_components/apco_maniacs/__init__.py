"""Optional APCO Weather backend; the standalone card remains independent."""
from homeassistant.const import Platform

from .coordinator import APCOCoordinator
from .frontend import async_register_card

PLATFORMS = [Platform.SENSOR]


async def async_setup(hass, config):
    """Register the shared card once, before setting up location entries."""
    await async_register_card(hass)
    return True


async def async_setup_entry(hass, entry):
    """Set up one coordinator per configured location."""
    coordinator = APCOCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass, entry):
    """CoordinatorEntity removes subscriptions and stops polling on unload."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass, entry):
    """Apply location and threshold changes."""
    await hass.config_entries.async_reload(entry.entry_id)
