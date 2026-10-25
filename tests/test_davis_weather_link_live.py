from datetime import datetime, timezone

import pytest

from custom_components.davis_weatherlink_live.davis_weatherlink_live import (
    DavisApiError,
    DavisWeatherLinkLive,
)


class TestDavisWeatherLinkLive:
    def setup_method(self):
        self.davis = DavisWeatherLinkLive(None, None, "entry1")

    def test_unix_to_datetime(self):
        expected_date_time = datetime(2015, 10, 21, 4, 0, tzinfo=timezone.utc)
        assert self.davis.unix_to_datetime(1445400000) == expected_date_time

    def test_unix_to_datetime_non_numeric_input(self):
        assert self.davis.unix_to_datetime("123") is None

    def test_battery_low_status(self):
        assert self.davis.battery_low_status(0) == "No"
        assert self.davis.battery_low_status(1) == "Yes"
        assert self.davis.battery_low_status(-1) is None
        assert self.davis.battery_low_status(2) is None
        assert self.davis.battery_low_status("string") is None
        assert self.davis.battery_low_status(None) is None

    def test_wind_dir_to_rose(self):
        assert self.davis.wind_dir_to_rose(45) == "NE"
        assert self.davis.wind_dir_to_rose(135) == "SE"
        assert self.davis.wind_dir_to_rose(360) == "N"

    def test_calculate_rain_amount(self):
        assert self.davis.calculate_rain_amount(10, 1) == pytest.approx(0.1)
        assert self.davis.calculate_rain_amount(10, 2) == pytest.approx(2.0)
        assert self.davis.calculate_rain_amount(None, 1) == 0.0
        assert self.davis.calculate_rain_amount(10, None) is None  # unknown cup size

    def test_parse_rejects_bad_payloads(self):
        for payload in ({"data": None}, {"data": {}}, {"data": {"conditions": []}, "error": "busy"}):
            with pytest.raises(DavisApiError):
                self.davis.parse_weather_data(payload)

    def test_parse_iss_record(self):
        payload = {
            "data": {
                "conditions": [
                    {"data_structure_type": 1, "txid": 1, "temp": 62.7, "rain_size": 1, "rainfall_daily": 5}
                ]
            },
            "error": None,
        }
        data = self.davis.parse_weather_data(payload)
        assert data["temp_tx1"] == 62.7
        assert data["data_structure_type_tx1"] == 1
        assert data["rainfall_daily_tx1"] == pytest.approx(0.05)

        # AirLink reports "no error" as 0 instead of null
        payload["error"] = 0
        assert self.davis.parse_weather_data(payload)["temp_tx1"] == 62.7
