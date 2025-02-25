"""Sensor platform for Davis WeatherLink Live integration."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorStateClass,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolumetricFlux,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MyConfigEntry
from .const import DOMAIN
from .coordinator import WeatherCoordinator

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="lsid",
        translation_key="lsid",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_visible_default=False,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="txid",
        translation_key="txid",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_visible_default=False,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="temp",
        translation_key="temp",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="hum",
        translation_key="hum",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="dew_point",
        translation_key="dew_point",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wet_bulb",
        translation_key="wet_bulb",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="heat_index",
        translation_key="heat_index",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wind_chill",
        translation_key="wind_chill",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="thw_index",
        translation_key="thw_index",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="thsw_index",
        translation_key="thsw_index",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_visible_default=False,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="wind_speed_last",
        translation_key="wind_speed_last",
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wind_dir_last",
        translation_key="wind_dir_last",
        native_unit_of_measurement=DEGREE,
        icon="mdi:compass-outline",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wind_dir_last_rose",
        translation_key="wind_dir_last_rose",
        icon="mdi:compass-outline",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wind_speed_avg_last_1_min",
        translation_key="wind_speed_avg_last_1_min",
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wind_dir_scalar_avg_last_1_min",
        translation_key="wind_dir_scalar_avg_last_1_min",
        native_unit_of_measurement=DEGREE,
        icon="mdi:compass-outline",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wind_speed_avg_last_2_min",
        translation_key="wind_speed_avg_last_2_min",
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wind_dir_scalar_avg_last_2_min",
        translation_key="wind_dir_scalar_avg_last_2_min",
        native_unit_of_measurement=DEGREE,
        icon="mdi:compass-outline",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wind_speed_hi_last_2_min",
        translation_key="wind_speed_hi_last_2_min",
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wind_dir_at_hi_speed_last_2_min",
        translation_key="wind_dir_at_hi_speed_last_2_min",
        native_unit_of_measurement=DEGREE,
        icon="mdi:compass-outline",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wind_speed_avg_last_10_min",
        translation_key="wind_speed_avg_last_10_min",
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wind_dir_scalar_avg_last_10_min",
        translation_key="wind_dir_scalar_avg_last_10_min",
        native_unit_of_measurement=DEGREE,
        icon="mdi:compass-outline",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wind_dir_scalar_avg_last_10_min_rose",
        translation_key="wind_dir_scalar_avg_last_10_min_rose",
        icon="mdi:compass-outline",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wind_speed_hi_last_10_min",
        translation_key="wind_speed_hi_last_10_min",
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wind_dir_at_hi_speed_last_10_min",
        translation_key="wind_dir_at_hi_speed_last_10_min",
        native_unit_of_measurement=DEGREE,
        icon="mdi:compass-outline",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="rain_size",
        translation_key="rain_size",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_visible_default=False,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="rain_rate_last",
        translation_key="rain_rate_last",
        native_unit_of_measurement=UnitOfVolumetricFlux.INCHES_PER_HOUR,
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="rain_rate_hi",
        translation_key="rain_rate_hi",
        native_unit_of_measurement=UnitOfVolumetricFlux.INCHES_PER_HOUR,
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="rainfall_last_15_min",
        translation_key="rainfall_last_15_min",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="rain_rate_hi_last_15_min",
        translation_key="rain_rate_hi_last_15_min",
        native_unit_of_measurement=UnitOfVolumetricFlux.INCHES_PER_HOUR,
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="rainfall_last_60_min",
        translation_key="rainfall_last_60_min",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="rainfall_last_24_hr",
        translation_key="rainfall_last_24_hr",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="rain_storm",
        translation_key="rain_storm",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="rain_storm_start_at",
        translation_key="rain_storm_start_at",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="solar_rad",
        translation_key="solar_rad",
        entity_registry_visible_default=False,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="uv_index",
        translation_key="uv_index",
        entity_registry_visible_default=False,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="rx_state",
        translation_key="rx_state",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="trans_battery_flag",
        translation_key="trans_battery_flag",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="rainfall_daily",
        translation_key="rainfall_daily",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.TOTAL,
    ),
    SensorEntityDescription(
        key="rainfall_monthly",
        translation_key="rainfall_monthly",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.TOTAL,
    ),
    SensorEntityDescription(
        key="rainfall_year",
        translation_key="rainfall_year",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.TOTAL,
    ),
    SensorEntityDescription(
        key="rain_storm_last",
        translation_key="rain_storm_last",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.TOTAL,
    ),
    SensorEntityDescription(
        key="rain_storm_last_start_at",
        translation_key="rain_storm_last_start_at",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="rain_storm_last_end_at",
        translation_key="rain_storm_last_end_at",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="temp_in",
        translation_key="temp_in",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="hum_in",
        translation_key="hum_in",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="dew_point_in",
        translation_key="dew_point_in",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key="heat_index_in",
        translation_key="heat_index_in",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="bar_sea_level",
        translation_key="bar_sea_level",
        native_unit_of_measurement=UnitOfPressure.INHG,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="bar_trend",
        translation_key="bar_trend",
        native_unit_of_measurement=UnitOfPressure.INHG,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="bar_absolute",
        translation_key="bar_absolute",
        native_unit_of_measurement=UnitOfPressure.INHG,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
    async_add_entities: AddEntitiesCallback,
):  # (hass, entry, async_add_entities):
    # coordinator = hass.data[DOMAIN][entry.entry_id]

    # This gets the data update coordinator from the config entry runtime data as specified in your __init__.py
    coordinator: WeatherCoordinator = config_entry.runtime_data.coordinator

    # Create a unique device ID based on the integration entry ID
    device_id = config_entry.entry_id

    sensors = [
        WeatherSensor(coordinator, description, device_id)
        for description in SENSOR_TYPES
    ]
    async_add_entities(sensors)


class WeatherSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = (
        True  # Allows entity names to be customized as sensor.deviceName_descriptionKey
    )

    def __init__(
        self, coordinator, description: SensorEntityDescription, device_id: str
    ):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{description.key}"
        self._device_id = device_id  # Store the device ID to link together

    @property
    def native_value(self):
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": "Davis Weather",
            "manufacturer": "Davis Instruments",
            "model": "WeatherLink Live 6100",
            "sw_version": "1.0",  # Update with actual firmware version if available
        }