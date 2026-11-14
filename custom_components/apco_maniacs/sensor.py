"""Forecast/assessment plus numeric entities for Home Assistant automations."""
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfSpeed, UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, NAME
from .data import assessment, current_values

DESCRIPTIONS = (
    SensorEntityDescription(key="conditions", translation_key="conditions", device_class=SensorDeviceClass.ENUM,
                            options=["good", "bad", "unknown"], icon="mdi:paragliding"),
    SensorEntityDescription(key="temperature", translation_key="temperature", device_class=SensorDeviceClass.TEMPERATURE,
                            native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="wind", translation_key="wind", device_class=SensorDeviceClass.WIND_SPEED,
                            native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND, suggested_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="precipitation", translation_key="precipitation", native_unit_of_measurement=PERCENTAGE,
                            state_class=SensorStateClass.MEASUREMENT, icon="mdi:weather-rainy"),
)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(APCOSensor(entry.runtime_data, entry, description) for description in DESCRIPTIONS)


class APCOSensor(CoordinatorEntity, SensorEntity):
    """A location's sensor; only the conditions entity carries the forecast."""
    _attr_has_entity_name = True
    _attr_attribution = "Weather data by Open-Meteo (CC BY 4.0)"
    _unrecorded_attributes = frozenset({"forecast"})

    def __init__(self, coordinator, entry, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)}, name=f"{NAME} {coordinator.settings['name']}",
            manufacturer=NAME, model="Open-Meteo", entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def available(self):
        return (super().available and self.coordinator.updated_at is not None
                and 0 <= dt_util.utcnow().timestamp() - self.coordinator.updated_at <= 1800)

    @property
    def native_value(self):
        values = current_values(self.coordinator.data, dt_util.utcnow().timestamp())
        return assessment(values, self.coordinator.settings) if self.entity_description.key == "conditions" else values[self.entity_description.key]

    @property
    def extra_state_attributes(self):
        if self.entity_description.key != "conditions":
            return None
        return {
            "apco_maniacs": True,
            "forecast": self.coordinator.data,
            "updated_at": self.coordinator.updated_at,
            "location": self.coordinator.settings,
        }
