"""Davis WeatherLink Live API client."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from .const import API_TIMEOUT

_LOGGER = logging.getLogger(__name__)

# WeatherLink API Reference: https://weatherlink.github.io/weatherlink-live-local-api/
# https://github.com/weatherlink/weatherlink-live-local-api/blob/master/API.md

# AirLink API Reference: https://weatherlink.github.io/airlink-local-api/
# https://github.com/weatherlink/airlink-local-api/blob/master/index.md


class DavisWeatherLinkLive:
    def __init__(self, api_url, websession):
        self.api_url = api_url
        self.injected_websession = websession

    # POSIX / unix timestamp to datetime object
    @staticmethod
    def unix_to_datetime(unix_timestamp: int) -> datetime:
        try:
            return (
                datetime.fromtimestamp(unix_timestamp, timezone.utc)
                if isinstance(unix_timestamp, (int, float))
                else None
            )
        except (OSError, ValueError):  # Handle invalid timestamps
            return None

    @staticmethod
    def battery_low_status(value: int) -> str | None:
        return {0: "No", 1: "Yes"}.get(value)

    @staticmethod
    def rx_state_description(value: int) -> str | None:
        return {0: "Receiving Data", 1: "Missing Packets", 2: "Signal Lost"}.get(value)

    @staticmethod
    def wind_dir_to_rose(degrees: int) -> str | None:
        if not isinstance(degrees, (int, float)):
            return None
        directions = (
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
        )
        return directions[round(degrees / 22.5) % 16]

    @staticmethod
    def rain_size_description(rain_size: int) -> str | None:
        return {1: '0.01"', 2: "0.2 mm", 3: "0.1 mm", 4: '0.001"'}.get(rain_size)

    # Rainfall amount calculation based on rain value depending on cup size of weather station
    @staticmethod
    def calculate_rain_amount(rain_amount: int, rain_unit: int) -> float:
        # Check for valid cup size indicator
        if rain_unit not in range(1, 5):
            raise ValueError("cup size indicator must be between 1 and 4")

        # Check for valid rain amount as rain can't be negative or null
        if not isinstance(rain_amount, (int, float)) or rain_amount <= 0:
            return 0.0

        conversion_factors = {1: 0.01, 2: 0.2, 3: 0.1, 4: 0.001}
        return rain_amount * conversion_factors.get(rain_unit, 0)

    @staticmethod
    def zero_if_none(value: int | None) -> int:
        return 0 if value is None else value

    @staticmethod
    def zero_float_if_none(value: float | None) -> float:
        return 0.0 if value is None else value

    def parse_weather_data(self, data: dict) -> dict:
        _LOGGER.debug("Parsing weather data: %s", data)

        weather_data = {}

        # Check if the API response is all wrong
        if data.get("data", {}) is None:
            _LOGGER.error("Davis API response missing data object: %s", data.get("error"))
            return weather_data
        elif data.get("data", {}).get("conditions") is None:
            _LOGGER.error("Davis API response missing conditions object: %s", data.get("error"))
            return weather_data

        weather_data.update(
            {
                "raw_api": data,
            }
        )
        for condition in data.get("data", {}).get("conditions", []):
            data_type = condition.get("data_structure_type")

            if data_type == 1:  # ISS Current Conditions record (outside)
                unique_key = f"_tx{condition.get('txid')}"
                weather_data.update(
                    {
                        "lsid" + unique_key: condition.get("lsid"),
                        "txid" + unique_key: condition.get("txid"),
                        "temp" + unique_key: condition.get("temp"),
                        "hum" + unique_key: condition.get("hum"),
                        "dew_point" + unique_key: condition.get("dew_point"),
                        "wet_bulb" + unique_key: condition.get("wet_bulb"),
                        "heat_index" + unique_key: condition.get("heat_index"),
                        "wind_chill" + unique_key: condition.get("wind_chill"),
                        "thw_index" + unique_key: condition.get("thw_index"),
                        "thsw_index" + unique_key: condition.get("thsw_index"),
                        "wind_speed_last" + unique_key: condition.get(
                            "wind_speed_last"
                        ),
                        "wind_dir_last" + unique_key: condition.get("wind_dir_last"),
                        "wind_dir_last_rose"
                        + unique_key: DavisWeatherLinkLive.wind_dir_to_rose(
                            condition.get("wind_dir_last")
                        ),
                        "wind_speed_avg_last_1_min" + unique_key: condition.get(
                            "wind_speed_avg_last_1_min"
                        ),
                        "wind_dir_scalar_avg_last_1_min" + unique_key: condition.get(
                            "wind_dir_scalar_avg_last_1_min"
                        ),
                        "wind_speed_avg_last_2_min" + unique_key: condition.get(
                            "wind_speed_avg_last_2_min"
                        ),
                        "wind_dir_scalar_avg_last_2_min" + unique_key: condition.get(
                            "wind_dir_scalar_avg_last_2_min"
                        ),
                        "wind_speed_hi_last_2_min"
                        + unique_key: DavisWeatherLinkLive.zero_float_if_none(
                            condition.get(
                                "wind_speed_hi_last_2_min"
                            )  # bug in API sometimes throws a null when zero wind
                        ),
                        "wind_dir_at_hi_speed_last_2_min"
                        + unique_key: DavisWeatherLinkLive.zero_if_none(
                            condition.get(
                                "wind_dir_at_hi_speed_last_2_min"
                            )  # bug in API sometimes throws a null when zero wind
                        ),
                        "wind_speed_avg_last_10_min" + unique_key: condition.get(
                            "wind_speed_avg_last_10_min"
                        ),
                        "wind_dir_scalar_avg_last_10_min" + unique_key: condition.get(
                            "wind_dir_scalar_avg_last_10_min"
                        ),
                        "wind_dir_scalar_avg_last_10_min_rose"
                        + unique_key: DavisWeatherLinkLive.wind_dir_to_rose(
                            condition.get("wind_dir_scalar_avg_last_10_min")
                        ),
                        "wind_speed_hi_last_10_min" + unique_key: condition.get(
                            "wind_speed_hi_last_10_min"
                        ),
                        "wind_dir_at_hi_speed_last_10_min" + unique_key: condition.get(
                            "wind_dir_at_hi_speed_last_10_min"
                        ),
                        "rain_size" + unique_key: condition.get("rain_size"),
                        "rain_size_desc"
                        + unique_key: DavisWeatherLinkLive.rain_size_description(
                            condition.get("rain_size")
                        ),
                        "rain_rate_last"
                        + unique_key: DavisWeatherLinkLive.calculate_rain_amount(
                            condition.get("rain_rate_last"), condition.get("rain_size")
                        ),
                        "rain_rate_hi"
                        + unique_key: DavisWeatherLinkLive.calculate_rain_amount(
                            condition.get("rain_rate_hi"), condition.get("rain_size")
                        ),
                        "rainfall_last_15_min"
                        + unique_key: DavisWeatherLinkLive.calculate_rain_amount(
                            condition.get("rainfall_last_15_min"),
                            condition.get("rain_size"),
                        ),
                        "rain_rate_hi_last_15_min"
                        + unique_key: DavisWeatherLinkLive.calculate_rain_amount(
                            condition.get("rain_rate_hi_last_15_min"),
                            condition.get("rain_size"),
                        ),
                        "rainfall_last_60_min"
                        + unique_key: DavisWeatherLinkLive.calculate_rain_amount(
                            condition.get("rainfall_last_60_min"),
                            condition.get("rain_size"),
                        ),
                        "rainfall_last_24_hr"
                        + unique_key: DavisWeatherLinkLive.calculate_rain_amount(
                            condition.get("rainfall_last_24_hr"),
                            condition.get("rain_size"),
                        ),
                        "rain_storm"
                        + unique_key: DavisWeatherLinkLive.calculate_rain_amount(
                            condition.get("rain_storm"), condition.get("rain_size")
                        ),
                        "rain_storm_start_at"
                        + unique_key: DavisWeatherLinkLive.unix_to_datetime(
                            condition.get("rain_storm_start_at")
                        ),
                        "solar_rad" + unique_key: condition.get("solar_rad"),
                        "uv_index" + unique_key: condition.get("uv_index"),
                        "rx_state"
                        + unique_key: DavisWeatherLinkLive.rx_state_description(
                            condition.get("rx_state")
                        ),
                        "trans_battery_flag"
                        + unique_key: DavisWeatherLinkLive.battery_low_status(
                            condition.get("trans_battery_flag")
                        ),
                        "rainfall_daily"
                        + unique_key: DavisWeatherLinkLive.calculate_rain_amount(
                            condition.get("rainfall_daily"), condition.get("rain_size")
                        ),
                        "rainfall_monthly"
                        + unique_key: DavisWeatherLinkLive.calculate_rain_amount(
                            condition.get("rainfall_monthly"),
                            condition.get("rain_size"),
                        ),
                        "rainfall_year"
                        + unique_key: DavisWeatherLinkLive.calculate_rain_amount(
                            condition.get("rainfall_year"), condition.get("rain_size")
                        ),
                        "rain_storm_last"
                        + unique_key: DavisWeatherLinkLive.calculate_rain_amount(
                            condition.get("rain_storm_last"), condition.get("rain_size")
                        ),
                        "rain_storm_last_start_at"
                        + unique_key: DavisWeatherLinkLive.unix_to_datetime(
                            condition.get("rain_storm_last_start_at")
                        ),
                        "rain_storm_last_end_at"
                        + unique_key: DavisWeatherLinkLive.unix_to_datetime(
                            condition.get("rain_storm_last_end_at")
                        ),
                    }
                )

            elif data_type == 2:  # Moisture Current Conditions record
                unique_key = f"_tx{condition.get('txid')}"
                weather_data.update(
                    {
                        "lsid" + unique_key: condition.get("lsid"),
                        "txid" + unique_key: condition.get("txid"),
                        "temp_1" + unique_key: condition.get("temp_1"),
                        "temp_2" + unique_key: condition.get("temp_2"),
                        "temp_3" + unique_key: condition.get("temp_3"),
                        "temp_4" + unique_key: condition.get("temp_4"),
                        "moist_soil_1" + unique_key: condition.get("moist_soil_1"),
                        "moist_soil_2" + unique_key: condition.get("moist_soil_2"),
                        "moist_soil_3" + unique_key: condition.get("moist_soil_3"),
                        "moist_soil_4" + unique_key: condition.get("moist_soil_4"),
                        "wet_leaf_1" + unique_key: condition.get("wet_leaf_1"),
                        "wet_leaf_2" + unique_key: condition.get("wet_leaf_2"),
                        "rx_state"
                        + unique_key: DavisWeatherLinkLive.rx_state_description(
                            condition.get("rx_state")
                        ),
                        "trans_battery_flag"
                        + unique_key: DavisWeatherLinkLive.battery_low_status(
                            condition.get("trans_battery_flag")
                        ),
                    }
                )

            elif data_type == 3:  # LSS BAR Current Conditions record
                unique_id = condition.get("lsid")
                unique_key = f"_ls{unique_id}"
                weather_data.update(
                    {
                        "lsid" + unique_key: condition.get("lsid"),
                        "bar_sea_level" + unique_key: condition.get("bar_sea_level"),
                        "bar_trend" + unique_key: condition.get("bar_trend"),
                        "bar_absolute" + unique_key: condition.get("bar_absolute"),
                    }
                )

            elif data_type == 4:  # LSS Temp/Hum Current Conditions record (inside)
                unique_id = condition.get("lsid")
                unique_key = f"_ls{unique_id}"
                weather_data.update(
                    {
                        "lsid" + unique_key: condition.get("lsid"),
                        "temp_in" + unique_key: condition.get("temp_in"),
                        "hum_in" + unique_key: condition.get("hum_in"),
                        "dew_point_in" + unique_key: condition.get("dew_point_in"),
                        "heat_index_in" + unique_key: condition.get("heat_index_in"),
                    }
                )
                
            elif data_type == 6:  # Air Quality Monitor
                unique_id = condition.get("lsid")
                unique_key = f"_ls{unique_id}"
                weather_data.update(
                    {
                        "lsid" + unique_key: condition.get("lsid"),
                        "temp" + unique_key: condition.get("temp"),
                        "hum" + unique_key: condition.get("hum"),
                        "dew_point" + unique_key: condition.get("dew_point"),
                        "wet_bulb" + unique_key: condition.get("wet_bulb"),
                        "heat_index" + unique_key: condition.get("heat_index"),
                        "pm_1_last" + unique_key: condition.get("pm_1_last"),
                        "pm_2p5_last" + unique_key: condition.get("pm_2p5_last"),
                        "pm_10_last" + unique_key: condition.get("pm_10_last"),
                        "pm_1" + unique_key: condition.get("pm_1"),
                        "pm_2p5" + unique_key: condition.get("pm_2p5"),
                        "pm_10" + unique_key: condition.get("pm_10"),
                        "pm_2p5_last_1_hour" + unique_key: condition.get(
                            "pm_2p5_last_1_hour"
                        ),
                        "pm_2p5_last_3_hours" + unique_key: condition.get(
                            "pm_2p5_last_3_hours"
                        ),
                        "pm_2p5_nowcast" + unique_key: condition.get(
                            "pm_2p5_nowcast"
                        ),
                        "pm_2p5_last_24_hours" + unique_key: condition.get(
                            "pm_2p5_last_24_hours"
                        ),
                        "pm_10_last_1_hour" + unique_key: condition.get(
                            "pm_10_last_1_hour"
                        ),
                        "pm_10_last_3_hours" + unique_key: condition.get(
                            "pm_10_last_3_hours"
                        ),
                        "pm_10_nowcast" + unique_key: condition.get("pm_10_nowcast"),
                        "pm_10_last_24_hours" + unique_key: condition.get(
                            "pm_10_last_24_hours"
                        ),
                        "last_report_time" + unique_key: DavisWeatherLinkLive.unix_to_datetime(
                            condition.get("last_report_time")
                        ),
                        "pct_pm_data_last_1_hour" + unique_key: condition.get(
                            "pct_pm_data_last_1_hour"
                        ),
                        "pct_pm_data_last_3_hours" + unique_key: condition.get(
                            "pct_pm_data_last_3_hours"
                        ),
                        "pct_pm_data_nowcast" + unique_key: condition.get(
                            "pct_pm_data_nowcast"
                        ),
                        "pct_pm_data_last_24_hours" + unique_key: condition.get(
                            "pct_pm_data_last_24_hours"
                        ),
                    }
                )

        _LOGGER.debug("Formatted weather data: %s", weather_data)

        return weather_data

    async def get_weather_data(self):
        """Fetch weather data from API and parse JSON response."""

        # Old Requests based method
        # response = requests.get(self.api_url, timeout=API_TIMEOUT)
        # if response.status_code != 200:
        #    raise Exception(f"API request failed with status {response.status_code}")

        # data = response.json()
        # return self.parse_weather_data(data)

        # New injected-websession based method, cool!

        async with self.injected_websession.get(
            self.api_url, timeout=API_TIMEOUT
        ) as response:
            if response.status != 200:
                raise Exception(
                    f"Weather API request failed with status {response.status}"
                )
            return self.parse_weather_data(await response.json())
