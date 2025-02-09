from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorDeviceClass
from homeassistant.const import UnitOfTemperature, PERCENTAGE, UnitOfPressure, UnitOfSpeed, UnitOfLength, DEGREE
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="temp",
        name="Temperature",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key="hum",
        name="Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
    ),
    SensorEntityDescription(
        key="dew_point",
        name="Dew Point",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key="wet_bulb",
        name="Wet Bulb",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key="thw_index",
        name="THW Index",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key="wind_speed_last",
        name="Wind Speed",
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
    ),
    SensorEntityDescription(
        key="wind_dir_last",
        name="Wind Direction",
        native_unit_of_measurement=DEGREE,
        icon="mdi:compass-outline",
    ),
    SensorEntityDescription(
        key="wind_dir_last_rose",
        name="Wind Direction Rose",
        icon="mdi:compass-outline",
    ),
    SensorEntityDescription(
        key="wind_speed_avg_last_1_min",
        name="Wind Speed Avg Last Min",
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
    ),
    SensorEntityDescription(
        key="wind_dir_scalar_avg_last_1_min",
        name="Wind Direction Avg Last Min",
        native_unit_of_measurement=DEGREE,
        icon="mdi:compass-outline",
    ),
    SensorEntityDescription(
        key="wind_speed_avg_last_2_min",
        name="Wind Speed Avg Last 2 Min",
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
    ),
    SensorEntityDescription(
        key="wind_dir_scalar_avg_last_2_min",
        name="Wind Direction Avg Last 2 Min",
        native_unit_of_measurement=DEGREE,
        icon="mdi:compass-outline",
    ),
    SensorEntityDescription(
        key="wind_speed_hi_last_2_min",
        name="Wind Gust Last 2 Min",
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
    ),
    SensorEntityDescription(
        key="wind_dir_at_hi_speed_last_2_min",
        name="Wind Gust Direction Last 2 Min",
        native_unit_of_measurement=DEGREE,
        icon="mdi:compass-outline",
    ),
    SensorEntityDescription(
        key="wind_speed_avg_last_10_min",
        name="Wind Speed Avg Last 10 Min",
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
    ),
    SensorEntityDescription(
        key="wind_dir_scalar_avg_last_10_min",
        name="Wind Direction Avg Last 10 Min",
        native_unit_of_measurement=DEGREE,
        icon="mdi:compass-outline",
    ),
    SensorEntityDescription(
        key="wind_dir_scalar_avg_last_10_min_rose",
        name="Wind Direction Avg Last 10 Min Rose",
        icon="mdi:compass-outline",
    ),
    SensorEntityDescription(
        key="wind_speed_hi_last_10_min",
        name="Wind Gust Last 10 Min",
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
    ),
    SensorEntityDescription(
        key="wind_dir_at_hi_speed_last_10_min",
        name="Wind Gust Direction Last 10 Min",
        native_unit_of_measurement=DEGREE,
        icon="mdi:compass-outline",
    ),
    SensorEntityDescription(
        key="rain_size",
        name="Rain Cup Size",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_visible_default=False,
    ),
    SensorEntityDescription(
        key="rain_rate_last",
        name="Rain Rate Latest",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
    ),
    SensorEntityDescription(
        key="rain_rate_hi",
        name="Rain Rate High",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
    ),
    SensorEntityDescription(
        key="rainfall_last_15_min",
        name="Rainfall Last 15 Min",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
    ),
    SensorEntityDescription(
        key="rain_rate_hi_last_15_min",
        name="Rain Rate Last 15 Min",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
    ),
    SensorEntityDescription(
        key="rainfall_last_60_min",
        name="Rainfall Last Hour",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
    ),
    SensorEntityDescription(
        key="rainfall_last_24_hr",
        name="Rainfall Last 24 Hours",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
    ),
    SensorEntityDescription(
        key="rain_storm",
        name="Rainfall Storm",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
    ),
    SensorEntityDescription(
        key="rain_storm_start_at",
        name="Rain Storm At",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="rx_state",
        name="ISS RX Status",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="trans_battery_flag",
        name="ISS Battery Low",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="rainfall_daily",
        name="Rainfall Day",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
    ),
    SensorEntityDescription(
        key="rainfall_monthly",
        name="Rainfall Month",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
    ),
    SensorEntityDescription(
        key="rainfall_year",
        name="Rainfall Year",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
    ),
    SensorEntityDescription(
        key="rain_storm_last",
        name="Rainfall Last Storm",
        native_unit_of_measurement=UnitOfLength.INCHES,
        device_class=SensorDeviceClass.PRECIPITATION,
    ),
    SensorEntityDescription(
        key="rain_storm_last_start_at",
        name="Rain Storm Start",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="rain_storm_last_end_at",
        name="Rain Storm End",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="temp_in",
        name="Indoor Temperature",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key="hum_in",
        name="Indoor Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
    ),
    SensorEntityDescription(
        key="dew_point_in",
        name="Indoor Dew Point",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key="heat_index_in",
        name="Indoor Heat Index",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorEntityDescription(
        key="bar_sea_level",
        name="Bar Sea Level Pressure",
        native_unit_of_measurement=UnitOfPressure.INHG,
        device_class=SensorDeviceClass.PRESSURE,
    ),
    SensorEntityDescription(
        key="bar_trend",
        name="Bar Trend Pressure",
        native_unit_of_measurement=UnitOfPressure.INHG,
        device_class=SensorDeviceClass.PRESSURE,
    ),
    SensorEntityDescription(
        key="bar_absolute",
        name="Bar Absolute Pressure",
        native_unit_of_measurement=UnitOfPressure.INHG,
        device_class=SensorDeviceClass.PRESSURE,
    ),
)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Create a unique device ID based on the integration entry ID
    device_id = entry.entry_id

    sensors = [WeatherSensor(coordinator, description, device_id) for description in SENSOR_TYPES]
    async_add_entities(sensors)

class WeatherSensor(CoordinatorEntity, SensorEntity):

    _attr_has_entity_name = True # Allows entity names to be customized as sensor.deviceName_descriptionKey 

    def __init__(self, coordinator, description: SensorEntityDescription, device_id: str):
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