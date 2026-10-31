"""Sensor platform for Davis WeatherLink Live integration."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    UnitOfDensity,
    UnitOfIrradiance,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolumetricFlux,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MyConfigEntry
from .const import DOMAIN
from .coordinator import WeatherCoordinator
from .realtime import RealtimeListener, is_realtime_key

_LOGGER = logging.getLogger(__name__)

# Entities only read coordinator data; the coordinator does the polling
PARALLEL_UPDATES = 0


def get_device_name(condition: dict[str, Any]) -> str | None:
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
        case _:
            return None


# Device Sensor type helper that returns the correct sensors based on the device type
def get_device_sensors(
    condition: dict[str, Any], deviceID: str, did: str | None
) -> tuple[SensorEntityDescription, ...]:
    device_type = condition.get("data_structure_type")

    # Return the correct sensors based on the device type
    _LOGGER.debug(
        "get_device_sensors called with device_type: %s, condition value: %s",
        device_type,
        condition,
    )

    if device_type == 1:  # General weather outdoor sensors
        unique_id = condition.get("txid")
        unique_key = f"_tx{unique_id}_{did}"
        api_rain_size_value: Any = condition.get("rain_size")

        rain_rate_unit = {
            1: UnitOfVolumetricFlux.INCHES_PER_HOUR,
            2: UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
            3: UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
            4: UnitOfVolumetricFlux.INCHES_PER_HOUR,
        }.get(api_rain_size_value)
        rain_amount_unit = {
            1: UnitOfLength.INCHES,
            2: UnitOfLength.MILLIMETERS,
            3: UnitOfLength.MILLIMETERS,
            4: UnitOfLength.INCHES,
        }.get(api_rain_size_value)

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
                device_class=SensorDeviceClass.WIND_DIRECTION,
                state_class=SensorStateClass.MEASUREMENT_ANGLE,
            ),
            SensorEntityDescription(
                key="wind_dir_last_rose" + unique_key,
                translation_key="wind_dir_last_rose",
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
                device_class=SensorDeviceClass.WIND_DIRECTION,
                state_class=SensorStateClass.MEASUREMENT_ANGLE,
            ),
            SensorEntityDescription(
                key="wind_dir_scalar_avg_last_10_min_rose" + unique_key,
                translation_key="wind_dir_scalar_avg_last_10_min_rose",
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
                suggested_display_precision=2,
            ),
            SensorEntityDescription(
                key="rain_rate_hi" + unique_key,
                translation_key="rain_rate_hi",
                native_unit_of_measurement=rain_rate_unit,
                device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=2,
            ),
            SensorEntityDescription(
                key="rainfall_last_15_min" + unique_key,
                translation_key="rainfall_last_15_min",
                native_unit_of_measurement=rain_amount_unit,
                device_class=SensorDeviceClass.PRECIPITATION,
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=2,
            ),
            SensorEntityDescription(
                key="rain_rate_hi_last_15_min" + unique_key,
                translation_key="rain_rate_hi_last_15_min",
                native_unit_of_measurement=rain_rate_unit,
                device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=2,
            ),
            SensorEntityDescription(
                key="rainfall_last_60_min" + unique_key,
                translation_key="rainfall_last_60_min",
                native_unit_of_measurement=rain_amount_unit,
                device_class=SensorDeviceClass.PRECIPITATION,
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=2,
            ),
            SensorEntityDescription(
                key="rainfall_last_24_hr" + unique_key,
                translation_key="rainfall_last_24_hr",
                native_unit_of_measurement=rain_amount_unit,
                device_class=SensorDeviceClass.PRECIPITATION,
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=2,
            ),
            SensorEntityDescription(
                key="rain_storm" + unique_key,
                translation_key="rain_storm",
                native_unit_of_measurement=rain_amount_unit,
                device_class=SensorDeviceClass.PRECIPITATION,
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=2,
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
                state_class=SensorStateClass.TOTAL_INCREASING,
                suggested_display_precision=2,
            ),
            SensorEntityDescription(
                key="rainfall_monthly" + unique_key,
                translation_key="rainfall_monthly",
                native_unit_of_measurement=rain_amount_unit,
                device_class=SensorDeviceClass.PRECIPITATION,
                state_class=SensorStateClass.TOTAL_INCREASING,
                suggested_display_precision=2,
            ),
            SensorEntityDescription(
                key="rainfall_year" + unique_key,
                translation_key="rainfall_year",
                native_unit_of_measurement=rain_amount_unit,
                device_class=SensorDeviceClass.PRECIPITATION,
                state_class=SensorStateClass.TOTAL_INCREASING,
                suggested_display_precision=2,
            ),
            SensorEntityDescription(
                key="rain_storm_last" + unique_key,
                translation_key="rain_storm_last",
                native_unit_of_measurement=rain_amount_unit,
                device_class=SensorDeviceClass.PRECIPITATION,
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=2,
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

        return DST_1

    elif device_type == 2:  # Soil Moisture Sensors
        unique_id = condition.get("txid")
        unique_key = f"_tx{unique_id}_{did}"
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
                state_class=SensorStateClass.MEASUREMENT,
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
        unique_key = f"_ls{unique_id}{deviceID}"
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
                key="pm_1_last" + unique_key,
                translation_key="pm_1_last",
                native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
                device_class=SensorDeviceClass.PM1,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="pm_2p5_last" + unique_key,
                translation_key="pm_2p5_last",
                native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
                device_class=SensorDeviceClass.PM25,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="pm_10_last" + unique_key,
                translation_key="pm_10_last",
                native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
                device_class=SensorDeviceClass.PM10,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="pm_1" + unique_key,
                translation_key="pm_1",
                native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
                device_class=SensorDeviceClass.PM1,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="pm_2p5" + unique_key,
                translation_key="pm_2p5",
                native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
                device_class=SensorDeviceClass.PM25,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="pm_10" + unique_key,
                translation_key="pm_10",
                native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
                device_class=SensorDeviceClass.PM10,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="pm_2p5_last_1_hour" + unique_key,
                translation_key="pm_2p5_last_1_hour",
                native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
                device_class=SensorDeviceClass.PM25,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="pm_2p5_last_3_hours" + unique_key,
                translation_key="pm_2p5_last_3_hours",
                native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
                device_class=SensorDeviceClass.PM25,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="pm_2p5_nowcast" + unique_key,
                translation_key="pm_2p5_nowcast",
                native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
                device_class=SensorDeviceClass.PM25,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="pm_2p5_last_24_hours" + unique_key,
                translation_key="pm_2p5_last_24_hours",
                native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
                device_class=SensorDeviceClass.PM25,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="pm_10_last_1_hour" + unique_key,
                translation_key="pm_10_last_1_hour",
                native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
                device_class=SensorDeviceClass.PM10,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="pm_10_last_3_hours" + unique_key,
                translation_key="pm_10_last_3_hours",
                native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
                device_class=SensorDeviceClass.PM10,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="pm_10_nowcast" + unique_key,
                translation_key="pm_10_nowcast",
                native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
                device_class=SensorDeviceClass.PM10,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="pm_10_last_24_hours" + unique_key,
                translation_key="pm_10_last_24_hours",
                native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
                device_class=SensorDeviceClass.PM10,
                state_class=SensorStateClass.MEASUREMENT,
            ),
            SensorEntityDescription(
                key="last_report_time" + unique_key,
                translation_key="last_report_time",
                device_class=SensorDeviceClass.TIMESTAMP,
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
            SensorEntityDescription(
                key="pct_pm_data_last_1_hour" + unique_key,
                translation_key="pct_pm_data_last_1_hour",
                native_unit_of_measurement=PERCENTAGE,
                state_class=SensorStateClass.MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
            SensorEntityDescription(
                key="pct_pm_data_last_3_hours" + unique_key,
                translation_key="pct_pm_data_last_3_hours",
                native_unit_of_measurement=PERCENTAGE,
                state_class=SensorStateClass.MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
            SensorEntityDescription(
                key="pct_pm_data_nowcast" + unique_key,
                translation_key="pct_pm_data_nowcast",
                native_unit_of_measurement=PERCENTAGE,
                state_class=SensorStateClass.MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
            SensorEntityDescription(
                key="pct_pm_data_last_24_hours" + unique_key,
                translation_key="pct_pm_data_last_24_hours",
                native_unit_of_measurement=PERCENTAGE,
                state_class=SensorStateClass.MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        )
        return DST_6

    else:
        _LOGGER.warning("Unknown API device type %s", device_type)
        return tuple()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create sensors for every device in the API response, including ones added later."""
    coordinator = config_entry.runtime_data.coordinator
    entry_id = str(config_entry.entry_id)
    known_lsids: set[Any] = set()

    @callback
    def _add_new_devices() -> None:
        api_data = coordinator.data["raw_api"]["data"]
        did = api_data.get("did")
        sensors: list[WeatherSensor] = []
        for condition in api_data.get("conditions", []):
            lsid = condition.get("lsid")
            if lsid in known_lsids:
                continue
            known_lsids.add(lsid)
            device_id = entry_id + str(lsid)
            device_name = get_device_name(condition)
            sensors.extend(
                WeatherSensor(coordinator, description, device_id, device_name)
                for description in get_device_sensors(condition, entry_id, did)
            )
        if sensors:
            async_add_entities(sensors)

    _add_new_devices()
    # A transmitter added to the hub later shows up in a later poll
    config_entry.async_on_unload(coordinator.async_add_listener(_add_new_devices))


class WeatherSensor(CoordinatorEntity[WeatherCoordinator], SensorEntity):
    """A single value from the Davis API."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WeatherCoordinator,
        description: SensorEntityDescription,
        device_id: str,
        device_name: str | None,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = description.key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            manufacturer="Davis Instruments",
            model="Davis WeatherLink Live / AirLink",
        )

    @property
    def _realtime(self) -> RealtimeListener | None:
        entry = self.coordinator.config_entry
        return entry.runtime_data.realtime if entry else None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self._realtime and is_realtime_key(self.entity_description.key):
            self.async_on_remove(self._realtime.add_listener(self.async_write_ha_state))

    @property
    def native_value(self) -> StateType | datetime:
        key = self.entity_description.key
        value: StateType | datetime
        if self._realtime:
            fresh, value = self._realtime.value(key)
            if fresh:
                return value
        value = self.coordinator.data.get(key)
        return value
