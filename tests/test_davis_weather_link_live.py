import pytest
from custom_components.davis_weatherlink_live.davis_weatherlink_live import DavisWeatherLinkLive
from datetime import datetime, timezone

class TestDavisWeatherLinkLive:

    def setup_method(self):
        API_URL = None
        WEBSSESSION = None
        self.davis = DavisWeatherLinkLive(API_URL, WEBSSESSION)

    def test_unix_to_datetime(self):
        expected_date_time = datetime(2015, 10, 21, 4, 0, tzinfo=timezone.utc)
        result = self.davis.unix_to_datetime(1445400000)
        assert result == expected_date_time

    def test_unix_to_datetime_non_numeric_input(self):
        result = self.davis.unix_to_datetime("123")
        assert result is None

    def test_battery_low_status(self):
        # Test with a value that should return "No"
        assert self.davis.battery_low_status(0) == "No"
        
        # Test with a value that should return "Yes"
        assert self.davis.battery_low_status(1) == "Yes"
        
        # Test with an invalid value (should return None)
        assert self.davis.battery_low_status(-1) is None
        assert self.davis.battery_low_status(2) is None
        
        # Test with a non-integer value (should return None)
        assert self.davis.battery_low_status("string") is None
        assert self.davis.battery_low_status(None) is None

    
    def test_battery_low_status(self):
        # Test status should return "Yes" when value is 1
        print(self.davis.battery_low_status(1))
        assert self.davis.battery_low_status(1) == "Yes"
        
        # Test status should return "No" when value is 0
        assert self.davis.battery_low_status(0) == "No"
        
        # Test status should return None for invalid input values
        assert self.davis.battery_low_status(3) is None

    def test_wind_dir_to_rose(self):
        # Test with a valid angle in degrees
        assert self.davis.wind_dir_to_rose(45) == "NE"
        
        # Test with another valid angle in degrees
        assert self.davis.wind_dir_to_rose(135) == "SE"

        # Test with the maximum valid angle (360)
        assert self.davis.wind_dir_to_rose(360) == "N"
