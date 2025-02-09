from __future__ import annotations
from datetime import datetime, timezone
import requests

from .const import API_TIMEOUT

# API Reference: https://weatherlink.github.io/weatherlink-live-local-api/
# https://github.com/weatherlink/weatherlink-live-local-api/blob/master/API.md

class DavisWeatherLinkLive:
    def __init__(self, api_url):
        self.api_url = api_url

    # POSIX / unix timestamp to datetime object    
    @staticmethod
    def unix_to_datetime(unix_timestamp: int) -> datetime | None:
        try:
            return datetime.fromtimestamp(unix_timestamp, timezone.utc) if isinstance(unix_timestamp, (int, float)) else None
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
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
        )
        return directions[round(degrees / 22.5) % 16]
    
    @staticmethod
    def rain_size_description(rain_size: int) -> str | None:
        return {1: '0.01"', 2: '0.2 mm', 3: '0.1 mm', 4: '0.001"'}.get(rain_size)

    # Rainfall amount calculation based on rain value depending on cup size of weather station   
    @staticmethod
    def calculate_rain_amount(rain_amount: int, rain_unit: int) -> float | None:
        conversion_factors = {1: 0.01, 2: 0.2, 3: 0.1, 4: 0.001}
        return rain_amount * conversion_factors.get(rain_unit, 0) if rain_amount is not None else None

    def get_weather_data(self):
        """Fetch weather data from API and parse JSON response.""" 
        response = requests.get(self.api_url, timeout=API_TIMEOUT)
        if response.status_code != 200:
            raise Exception(f"API request failed with status {response.status_code}")

        data = response.json()

        # Initialize values with None (to handle missing fields)
        weather_data = {
            "temp": None, 
            "hum": None, 
            "dew_point": None,
            "wet_bulb": None, 
            "thw_index": None,
            #"thsw_index": None, # Requires Add-on Solar Sensor
            "wind_speed_last": None, 
            "wind_dir_last": None,
            "wind_dir_last_rose": None,
            "wind_speed_avg_last_1_min": None,
            "wind_dir_scalar_avg_last_1_min": None,
            "wind_speed_avg_last_2_min": None,
            "wind_dir_scalar_avg_last_2_min": None,
            "wind_speed_hi_last_2_min": None,
            "wind_dir_at_hi_speed_last_2_min": None,
            "wind_speed_avg_last_10_min": None,
            "wind_dir_scalar_avg_last_10_min": None,
            "wind_dir_scalar_avg_last_10_min_rose": None,
            "wind_speed_hi_last_10_min": None,
            "wind_dir_at_hi_speed_last_10_min": None,
            "rain_size": None,
            "rain_rate_last": None,
            "rain_rate_hi": None,
            "rainfall_last_15_min": None,
            "rain_rate_hi_last_15_min": None,
            "rainfall_last_60_min": None,
            "rainfall_last_24_hr": None,
            "rain_storm": None,
            "rain_storm_start_at": None,
            #"solar_rad": None, # Requires Add-on Solar Sensor
            #"uv_index": None, # Requires Add-on Solar Sensor
            "rx_state": None,
            "trans_battery_flag": None,
            "rainfall_daily": None,
            "rainfall_monthly": None,
            "rainfall_year": None,
            "rain_storm_last": None,
            "rain_storm_last_start_at": None,
            "rain_storm_last_end_at": None,
            "temp_in": None,
            "hum_in": None,
            "dew_point_in": None,
            "heat_index_in": None,
            "bar_sea_level": None,
            "bar_trend": None,
            "bar_absolute": None
        }

        for condition in data.get("data", {}).get("conditions", []):
            data_type = condition.get("data_structure_type")

            if data_type == 1:  # ISS Current Conditions record (outside)
                weather_data.update({
                    "temp": condition.get("temp"),
                    "hum": condition.get("hum"),
                    "dew_point": condition.get("dew_point"),
                    "wet_bulb": condition.get("wet_bulb"),
                    "heat_index": condition.get("heat_index"),
                    "wind_chill": condition.get("wind_chill"),
                    "thw_index": condition.get("thw_index"),
                    #"thsw_index": condition.get("temp"), # Requires Add-on Solar Sensor
                    "wind_speed_last": condition.get("wind_speed_last"),
                    "wind_dir_last": condition.get("wind_dir_last"),
                    "wind_dir_last_rose": DavisWeatherLinkLive.wind_dir_to_rose(condition.get("wind_dir_last")),
                    "wind_speed_avg_last_1_min": condition.get("wind_speed_avg_last_1_min"),
                    "wind_dir_scalar_avg_last_1_min": condition.get("wind_dir_scalar_avg_last_1_min"),
                    "wind_speed_avg_last_2_min": condition.get("wind_speed_avg_last_2_min"),
                    "wind_dir_scalar_avg_last_2_min": condition.get("wind_dir_scalar_avg_last_2_min"),
                    "wind_speed_hi_last_2_min": condition.get("wind_speed_hi_last_2_min"),
                    "wind_dir_at_hi_speed_last_2_min": condition.get("wind_dir_at_hi_speed_last_2_min"),
                    "wind_speed_avg_last_10_min": condition.get("wind_speed_avg_last_10_min"),
                    "wind_dir_scalar_avg_last_10_min": condition.get("wind_dir_scalar_avg_last_10_min"),
                    "wind_dir_scalar_avg_last_10_min_rose": DavisWeatherLinkLive.wind_dir_to_rose(condition.get("wind_dir_scalar_avg_last_10_min")),
                    "wind_speed_hi_last_10_min": condition.get("wind_speed_hi_last_10_min"),
                    "wind_dir_at_hi_speed_last_10_min": condition.get("wind_dir_at_hi_speed_last_10_min"),
                    "rain_size": DavisWeatherLinkLive.rain_size_description(condition.get("rain_size")),
                    "rain_rate_last": DavisWeatherLinkLive.calculate_rain_amount(condition.get("rain_rate_last"),condition.get("rain_size")),  
                    "rain_rate_hi": DavisWeatherLinkLive.calculate_rain_amount(condition.get("rain_rate_hi"), condition.get("rain_size")),
                    "rainfall_last_15_min": DavisWeatherLinkLive.calculate_rain_amount(condition.get("rainfall_last_15_min"), condition.get("rain_size")),
                    "rain_rate_hi_last_15_min": DavisWeatherLinkLive.calculate_rain_amount(condition.get("rain_rate_hi_last_15_min"), condition.get("rain_size")),
                    "rainfall_last_60_min": DavisWeatherLinkLive.calculate_rain_amount(condition.get("rainfall_last_60_min"), condition.get("rain_size")),
                    "rainfall_last_24_hr": DavisWeatherLinkLive.calculate_rain_amount(condition.get("rainfall_last_24_hr"), condition.get("rain_size")),
                    "rain_storm": DavisWeatherLinkLive.calculate_rain_amount(condition.get("rain_storm"), condition.get("rain_size")),
                    "rain_storm_start_at": DavisWeatherLinkLive.unix_to_datetime(condition.get("rain_storm_start_at")),
                    #"solar_rad": null, # Requires Add-on Solar Sensor
                    #"uv_index": null, # Requires Add-on Solar Sensor
                    "rx_state": DavisWeatherLinkLive.rx_state_description(condition.get("rx_state")),
                    "trans_battery_flag": DavisWeatherLinkLive.battery_low_status(condition.get("trans_battery_flag")),
                    "rainfall_daily":  DavisWeatherLinkLive.calculate_rain_amount(condition.get("rainfall_daily"), condition.get("rain_size")),
                    "rainfall_monthly": DavisWeatherLinkLive.calculate_rain_amount(condition.get("rainfall_monthly"), condition.get("rain_size")),
                    "rainfall_year":  DavisWeatherLinkLive.calculate_rain_amount(condition.get("rainfall_year"), condition.get("rain_size")),
                    "rain_storm_last":  DavisWeatherLinkLive.calculate_rain_amount(condition.get("rain_storm_last"), condition.get("rain_size")),
                    "rain_storm_last_start_at": DavisWeatherLinkLive.unix_to_datetime(condition.get("rain_storm_last_start_at")),
                    "rain_storm_last_end_at": DavisWeatherLinkLive.unix_to_datetime(condition.get("rain_storm_last_end_at")),
                })

            elif data_type == 4:  # LSS Temp/Hum Current Conditions record (inside)
                weather_data.update({
                    "temp_in": condition.get("temp_in"),
                    "hum_in": condition.get("hum_in"),
                    "dew_point_in": condition.get("dew_point_in"),
                    "heat_index_in": condition.get("heat_index_in"),
                })

            elif data_type == 3:  # LSS BAR Current Conditions record (inside)
                weather_data.update({
                    "bar_sea_level": condition.get("bar_sea_level"),
                    "bar_trend": condition.get("bar_trend"),
                    "bar_absolute": condition.get("bar_absolute"),
                })

        return weather_data