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
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolumetricFlux,
    UnitOfIrradiance,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MyConfigEntry
from .const import DOMAIN
from .coordinator import WeatherCoordinator

import logging

_LOGGER = logging.getLogger(__name__)


def get_device_name(condition: tuple):
    match condition.get("data_structure_type"):
        case 1:
            return "Davis ISS TX " + str(condition.get("txid"))
        case 2:
            return "Davis Leaf/Soil Moisture TX " + str(condition.get("txid"))
        case 3:
            return "Davis LSS BAR"  # + str(condition.get("lsid"))
        case 4:
            return "Davis LSS"  # + str(condition.get("lsid"))
        case 6:
            return "Davis AirLink AQM"  # + str(condition.get("lsid"))


# Device Sensor type helper that returns the correct sensors based on the device type
def get_device_sensors(condition: tuple):
    device_type = condition.get("data_structure_type")

    # Return the correct sensors based on the device type
    _LOGGER.debug(
        "get_device_sensors called with device_type: %s, condition value: %s",
        device_type,
        condition,
    )

    if device_type == 1:  # General weather outdoor sensors
        unique_id = condition.get("txid")
        unique_key = f"_tx{unique_id}"
        api_rain_size_value = condition.get("rain_size")

        # Get the unit for rain rate for
        #    "rain_rate_last",
        #    "rain_rate_hi",
        #    "rain_rate_hi_last_15_min",

        rain_rate_unit = None
        match api_rain_size_value:
            case 0:
                rain_rate_unit = None
            case 1:
                _LOGGER.debug(
                    "For condition type %s, and lsid %s, using imperial units with rain size id %s",
                    device_type,
                    condition.get("lsid"),
                    api_rain_size_value,
                )
                rain_rate_unit = UnitOfVolumetricFlux.INCHES_PER_HOUR
            case 2:
                _LOGGER.debug(
                    "For condition type %s, and lsid %s, using metric units with rain size id %s",
                    device_type,
                    condition.get("lsid"),
                    api_rain_size_value,
                )
                rain_rate_unit = UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR
            case 3:
                _LOGGER.debug(
                    "For condition type %s, and lsid %s, using metric units with rain size id %s",
                    device_type,
                    condition.get("lsid"),
                    api_rain_size_value,
                )
                rain_rate_unit = UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR
            case 4:
                _LOGGER.debug(
                    "For condition type %s, and lsid %s, using imperial units with rain size id %s",
                    device_type,
                    condition.get("lsid"),
                    api_rain_size_value,
                )
                rain_rate_unit = UnitOfVolumetricFlux.INCHES_PER_HOUR
            case _:
                rain_rate_unit = None

        # Get the unit for rain amount for
        #    "rainfall_last_15_min",
        #    "rainfall_last_60_min",
        #    "rainfall_last_24_hr",
        #    "rain_storm",
        #    "rainfall_daily",
        #    "rainfall_monthly",
        #    "rainfall_year",
        #    "rain_storm_last",

        rain_amount_unit = None
        match api_rain_size_value:
            case 0:
                rain_amount_unit = None
            case 1:
                rain_amount_unit = UnitOfLength.INCHES
            case 2:
                rain_amount_unit = UnitOfLength.MILLIMETERS
            case 3:
                rain_amount_unit = UnitOfLength.MILLIMETERS
            case 4:
                rain_amount_unit = UnitOfLength.INCHES
            case _:
                rain_amount_unit = None

        DST_1: tuple[SensorEntityDescription, ...] = (
            SensorEntityDescription(
                key="lsid" + unique_key,
                translation_key="lsid",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_visible_default=False,
                entity_registry_enabled_default=False,
            ),
            SensorEntityDescription(
                key="data_structure_type" + unique_key,
                translation_key="dst",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_visible_default=False,
                entity_registry_enabled_default=False,
            ),
            SensorEntityDescription(
                key="txid" + unique_key,
                translation_key="txid",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_visible_default=False,
                entity_registry_enabled_default=False,
            ),
            SensorEntityDescription(
                key="temp" + unique_key,
                translation_key="temp",
                native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="hum" + unique_key,
                translation_key="hum",
                native_unit_of_measurement=PERCENTAGE,
                device_class=SensorDeviceClass.HUMIDITY,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="dew_point" + unique_key,
                translation_key="dew_point",
                native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="wet_bulb" + unique_key,
                translation_key="wet_bulb",
                native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="heat_index" + unique_key,
                translation_key="heat_index",
                native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="wind_chill" + unique_key,
                translation_key="wind_chill",
                native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="thw_index" + unique_key,
                translation_key="thw_index",
                native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="thsw_index" + unique_key,
                translation_key="thsw_index",
                native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
                entity_registry_visible_default=False,
                entity_registry_enabled_default=False,
            ),
            SensorEntityDescription(
                key="wind_speed_last" + unique_key,
                translation_key="wind_speed_last",
                native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
                device_class=SensorDeviceClass.WIND_SPEED,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="wind_dir_last" + unique_key,
                translation_key="wind_dir_last",
                native_unit_of_measurement=DEGREE,
                icon="mdi:compass-outline",
                device_class=SensorDeviceClass.WIND_DIRECTION,
                state_class=SensorStateClass.MEASUREMENT_ANGLE,
            ),
            SensorEntityDescription(
                key="wind_dir_last_rose" + unique_key,
                translation_key="wind_dir_last_rose",
                icon="mdi:compass-outline",
            ),
            SensorEntityDescription(
                key="wind_speed_avg_last_1_min" + unique_key,
                translation_key="wind_speed_avg_last_1_min",
                native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
                device_class=SensorDeviceClass.WIND_SPEED,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="wind_dir_scalar_avg_last_1_min" + unique_key,
                translation_key="wind_dir_scalar_avg_last_1_min",
                native_unit_of_measurement=DEGREE,
                icon="mdi:compass-outline",
                device_class=SensorDeviceClass.WIND_DIRECTION,
                state_class=SensorStateClass.MEASUREMENT_ANGLE,
            ),
            SensorEntityDescription(
                key="wind_speed_avg_last_2_min" + unique_key,
                translation_key="wind_speed_avg_last_2_min",
                native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
                device_class=SensorDeviceClass.WIND_SPEED,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="wind_dir_scalar_avg_last_2_min" + unique_key,
                translation_key="wind_dir_scalar_avg_last_2_min",
                native_unit_of_measurement=DEGREE,
                icon="mdi:compass-outline",
                device_class=SensorDeviceClass.WIND_DIRECTION,
                state_class=SensorStateClass.MEASUREMENT_ANGLE,
            ),
            SensorEntityDescription(
                key="wind_speed_hi_last_2_min" + unique_key,
                translation_key="wind_speed_hi_last_2_min",
                native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
                device_class=SensorDeviceClass.WIND_SPEED,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="wind_dir_at_hi_speed_last_2_min" + unique_key,
                translation_key="wind_dir_at_hi_speed_last_2_min",
                native_unit_of_measurement=DEGREE,
                icon="mdi:compass-outline",
                device_class=SensorDeviceClass.WIND_DIRECTION,
                state_class=SensorStateClass.MEASUREMENT_ANGLE,
            ),
            SensorEntityDescription(
                key="wind_speed_avg_last_10_min" + unique_key,
                translation_key="wind_speed_avg_last_10_min",
                native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
                device_class=SensorDeviceClass.WIND_SPEED,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="wind_dir_scalar_avg_last_10_min" + unique_key,
                translation_key="wind_dir_scalar_avg_last_10_min",
                native_unit_of_measurement=DEGREE,
                icon="mdi:compass-outline",
                device_class=SensorDeviceClass.WIND_DIRECTION,
                state_class=SensorStateClass.MEASUREMENT_ANGLE,
            ),
            SensorEntityDescription(
                key="wind_dir_scalar_avg_last_10_min_rose" + unique_key,
                translation_key="wind_dir_scalar_avg_last_10_min_rose",
                icon="mdi:compass-outline",
            ),
            SensorEntityDescription(
                key="wind_speed_hi_last_10_min" + unique_key,
                translation_key="wind_speed_hi_last_10_min",
                native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
                device_class=SensorDeviceClass.WIND_SPEED,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="wind_dir_at_hi_speed_last_10_min" + unique_key,
                translation_key="wind_dir_at_hi_speed_last_10_min",
                native_unit_of_measurement=DEGREE,
                icon="mdi:compass-outline",
                device_class=SensorDeviceClass.WIND_DIRECTION,
                state_class=SensorStateClass.MEASUREMENT_ANGLE,
            ),
            SensorEntityDescription(
                key="rain_size" + unique_key,
                translation_key="rain_size",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_visible_default=False,
                entity_registry_enabled_default=False,
            ),
            SensorEntityDescription(
                key="rain_size_desc" + unique_key,
                translation_key="rain_size_desc",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_visible_default=False,
                entity_registry_enabled_default=False,
            ),
            SensorEntityDescription(
                key="rain_rate_last" + unique_key,
                translation_key="rain_rate_last",
                native_unit_of_measurement=rain_rate_unit,
                device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="rain_rate_hi" + unique_key,
                translation_key="rain_rate_hi",
                native_unit_of_measurement=rain_rate_unit,
                device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="rainfall_last_15_min" + unique_key,
                translation_key="rainfall_last_15_min",
                native_unit_of_measurement=rain_amount_unit,
                device_class=SensorDeviceClass.PRECIPITATION,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="rain_rate_hi_last_15_min" + unique_key,
                translation_key="rain_rate_hi_last_15_min",
                native_unit_of_measurement=rain_rate_unit,
                device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="rainfall_last_60_min" + unique_key,
                translation_key="rainfall_last_60_min",
                native_unit_of_measurement=rain_amount_unit,
                device_class=SensorDeviceClass.PRECIPITATION,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="rainfall_last_24_hr" + unique_key,
                translation_key="rainfall_last_24_hr",
                native_unit_of_measurement=rain_amount_unit,
                device_class=SensorDeviceClass.PRECIPITATION,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="rain_storm" + unique_key,
                translation_key="rain_storm",
                native_unit_of_measurement=rain_amount_unit,
                device_class=SensorDeviceClass.PRECIPITATION,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="rain_storm_start_at" + unique_key,
                translation_key="rain_storm_start_at",
                device_class=SensorDeviceClass.TIMESTAMP,
            ),
            SensorEntityDescription(
                key="solar_rad" + unique_key,
                translation_key="solar_rad",
                native_unit_of_measurement=UnitOfIrradiance.WATTS_PER_SQUARE_METER,
                entity_registry_visible_default=False,
                entity_registry_enabled_default=False,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="uv_index" + unique_key,
                translation_key="uv_index",
                entity_registry_visible_default=False,
                entity_registry_enabled_default=False,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="rx_state" + unique_key,
                translation_key="rx_state",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
            SensorEntityDescription(
                key="trans_battery_flag" + unique_key,
                translation_key="trans_battery_flag",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
            SensorEntityDescription(
                key="rainfall_daily" + unique_key,
                translation_key="rainfall_daily",
                native_unit_of_measurement=rain_amount_unit,
                device_class=SensorDeviceClass.PRECIPITATION,
                state_class=SensorStateClass.TOTAL,
            ),
            SensorEntityDescription(
                key="rainfall_monthly" + unique_key,
                translation_key="rainfall_monthly",
                native_unit_of_measurement=rain_amount_unit,
                device_class=SensorDeviceClass.PRECIPITATION,
                state_class=SensorStateClass.TOTAL,
            ),
            SensorEntityDescription(
                key="rainfall_year" + unique_key,
                translation_key="rainfall_year",
                native_unit_of_measurement=rain_amount_unit,
                device_class=SensorDeviceClass.PRECIPITATION,
                state_class=SensorStateClass.TOTAL,
            ),
            SensorEntityDescription(
                key="rain_storm_last" + unique_key,
                translation_key="rain_storm_last",
                native_unit_of_measurement=rain_amount_unit,
                device_class=SensorDeviceClass.PRECIPITATION,
                state_class=SensorStateClass.TOTAL,
            ),
            SensorEntityDescription(
                key="rain_storm_last_start_at" + unique_key,
                translation_key="rain_storm_last_start_at",
                device_class=SensorDeviceClass.TIMESTAMP,
            ),
            SensorEntityDescription(
                key="rain_storm_last_end_at" + unique_key,
                translation_key="rain_storm_last_end_at",
                device_class=SensorDeviceClass.TIMESTAMP,
            ),
        )

        # _LOGGER.debug("DST_1: %s", DST_1)
        return DST_1

    elif device_type == 2:  # Soil Moisture Sensors
        unique_id = condition.get("txid")
        unique_key = f"_tx{unique_id}"
        DST_2: tuple[SensorEntityDescription, ...] = (
            SensorEntityDescription(
                key="lsid" + unique_key,
                translation_key="lsid",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_visible_default=False,
                entity_registry_enabled_default=False,
            ),
            SensorEntityDescription(
                key="data_structure_type" + unique_key,
                translation_key="dst",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_visible_default=False,
                entity_registry_enabled_default=False,
            ),
            SensorEntityDescription(
                key="temp_1" + unique_key,
                translation_key="soil_temp_1",
                native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="temp_2" + unique_key,
                translation_key="soil_temp_2",
                native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="temp_3" + unique_key,
                translation_key="soil_temp_3",
                native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="temp_4" + unique_key,
                translation_key="soil_temp_4",
                native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="moist_soil_1" + unique_key,
                translation_key="moist_soil_1",
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="moist_soil_2" + unique_key,
                translation_key="moist_soil_2",
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="moist_soil_3" + unique_key,
                translation_key="moist_soil_3",
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="moist_soil_4" + unique_key,
                translation_key="moist_soil_4",
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="wet_leaf_1" + unique_key,
                translation_key="wet_leaf_1",
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="wet_leaf_2" + unique_key,
                translation_key="wet_leaf_2",
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="rx_state" + unique_key,
                translation_key="rx_state",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
            SensorEntityDescription(
                key="trans_battery_flag" + unique_key,
                translation_key="trans_battery_flag",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        )
        return DST_2

    elif device_type == 3:  # Pressure Sensors
        unique_id = condition.get("lsid")
        unique_key = f"_ls{unique_id}"
        # Device Sensor Type 3: Pressure Sensors
        DST_3: tuple[SensorEntityDescription, ...] = (
            SensorEntityDescription(
                key="lsid" + unique_key,
                translation_key="lsid",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_visible_default=False,
                entity_registry_enabled_default=False,
            ),
            SensorEntityDescription(
                key="data_structure_type" + unique_key,
                translation_key="dst",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_visible_default=False,
                entity_registry_enabled_default=False,
            ),
            SensorEntityDescription(
                key="bar_sea_level" + unique_key,
                translation_key="bar_sea_level",
                native_unit_of_measurement=UnitOfPressure.INHG,
                device_class=SensorDeviceClass.PRESSURE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="bar_trend" + unique_key,
                translation_key="bar_trend",
                native_unit_of_measurement=UnitOfPressure.INHG,
                device_class=SensorDeviceClass.PRESSURE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="bar_absolute" + unique_key,
                translation_key="bar_absolute",
                native_unit_of_measurement=UnitOfPressure.INHG,
                device_class=SensorDeviceClass.PRESSURE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
        )
        return DST_3

    elif device_type == 4:  # Indoor WeatherLink Live Conditions
        unique_id = condition.get("lsid")
        unique_key = f"_ls{unique_id}"
        # Device Sensor Type 4: Indoor WeatherLink Live Conditions
        DST_4: tuple[SensorEntityDescription, ...] = (
            SensorEntityDescription(
                key="lsid" + unique_key,
                translation_key="lsid",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_visible_default=False,
                entity_registry_enabled_default=False,
            ),
            SensorEntityDescription(
                key="data_structure_type" + unique_key,
                translation_key="dst",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_visible_default=False,
                entity_registry_enabled_default=False,
            ),
            SensorEntityDescription(
                key="temp_in" + unique_key,
                translation_key="temp_in",
                native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="hum_in" + unique_key,
                translation_key="hum_in",
                native_unit_of_measurement=PERCENTAGE,
                device_class=SensorDeviceClass.HUMIDITY,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="dew_point_in" + unique_key,
                translation_key="dew_point_in",
                native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
                device_class=SensorDeviceClass.TEMPERATURE,
            ),
            SensorEntityDescription(
                key="heat_index_in" + unique_key,
                translation_key="heat_index_in",
                native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
        )
        return DST_4

    elif device_type == 6:  # WeatherLink Air Quality Monitors
        unique_id = condition.get("lsid")
        unique_key = f"_ls{unique_id}"
        # Device Sensor Type 6: Weatherlink AQI Conditions
        DST_6: tuple[SensorEntityDescription, ...] = (
            SensorEntityDescription(
                key="lsid" + unique_key,
                translation_key="lsid",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_visible_default=False,
                entity_registry_enabled_default=False,
            ),
            SensorEntityDescription(
                key="data_structure_type" + unique_key,
                translation_key="dst",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_visible_default=False,
                entity_registry_enabled_default=False,
            ),
            SensorEntityDescription(
                key="temp" + unique_key,
                translation_key="temp",
                native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="hum" + unique_key,
                translation_key="hum",
                native_unit_of_measurement=PERCENTAGE,
                device_class=SensorDeviceClass.HUMIDITY,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="dew_point" + unique_key,
                translation_key="dew_point",
                native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
                device_class=SensorDeviceClass.TEMPERATURE,
            ),
            SensorEntityDescription(
                key="heat_index" + unique_key,
                translation_key="heat_index",
                native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="pm_1" + unique_key,
                translation_key="pm_1",
                native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                device_class=SensorDeviceClass.PM1,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="pm_2p5" + unique_key,
                translation_key="pm_2p5",
                native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                device_class=SensorDeviceClass.PM25,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="pm_10" + unique_key,
                translation_key="pm_10",
                native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                device_class=SensorDeviceClass.PM10,
                state_class=SensorStateClass.MEASUREMENT,
            ),
        )
        return DST_6


    else:
        _LOGGER.warning("Unknown API device type %s", device_type)
        return tuple()


# TODO - Device Sensor Type 2: Soil Moisture Sensors


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    # This gets the data update coordinator from the config entry runtime data as specified in your __init__.py
    coordinator: WeatherCoordinator = config_entry.runtime_data.coordinator

    # Get latest data from the API via the coordinator refresh
    # disabled as it was causing errors
    # await coordinator.async_request_refresh()

    # Get api data from the coordinator
    api_response = coordinator.data

    # Create a container for all sensors, and build the sensor list based on each condition in api response and device type
    for condition in (
        api_response.get("raw_api", {}).get("data", {}).get("conditions", [])
    ):
        device_id = str(config_entry.entry_id) + str(condition.get("lsid"))
        device_name = get_device_name(condition)
        sensors = [
            WeatherSensor(coordinator, description, device_id, device_name)
            for description in get_device_sensors(condition)
        ]
        async_add_entities(sensors)

    _LOGGER.debug("Sensory.py Coordinator API response: %s", api_response)


class WeatherSensor(CoordinatorEntity, SensorEntity):

    # Allow entity names to be customized as sensor.deviceName_descriptionKey
    _attr_has_entity_name = True 
    
    def __init__(
        self,
        coordinator,
        description: SensorEntityDescription,
        device_id: str,
        device_name: str,
    ):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{description.key}"
        self._device_id = device_id  # Store the device ID to link together
        self._device_name = device_name
        _LOGGER.debug(
            "Sensor %s created with unique ID %s for device %s",
            description.key,
            self._attr_unique_id,
            device_id,
        )

    @property
    def native_value(self):
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            # "name": "Davis Weather",
            "name": self._device_name,
            "manufacturer": "Davis Instruments",
            "model": "WeatherLink Live 6100",
            "sw_version": "1.0",  # Add actual firmware version if Davis ever updates API
        }
