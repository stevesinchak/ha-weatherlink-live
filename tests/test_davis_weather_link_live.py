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
        assert self.davis.calculate_rain_amount(0, 1) == 0.0
        assert self.davis.calculate_rain_amount(None, 1) is None  # missing data
        assert self.davis.calculate_rain_amount(10, None) is None  # unknown cup size

    def test_parse_rejects_bad_payloads(self):
        for payload in ({"data": None}, {"data": {}}, {"data": {"conditions": []}, "error": "busy"}):
            with pytest.raises(DavisApiError):
                self.davis.parse_weather_data(payload)

    def test_parse_null_rain(self):
        # Null yearly total must stay unknown (a 0 would look like a reset to HA)
        payload = {
            "data": {
                "did": "D1",
                "conditions": [
                    {"data_structure_type": 1, "txid": 1, "rain_size": 1, "rainfall_year": None, "rain_storm": None}
                ]
            },
            "error": None,
        }
        data = self.davis.parse_weather_data(payload)
        assert data["rainfall_year_tx1_D1"] is None
        assert data["rain_storm_tx1_D1"] == 0.0  # null means no storm in progress

    def test_parse_iss_record(self):
        payload = {
            "data": {
                "did": "D1",
                "conditions": [
                    {"data_structure_type": 1, "txid": 1, "temp": 62.7, "rain_size": 1, "rainfall_daily": 5}
                ]
            },
            "error": None,
        }
        data = self.davis.parse_weather_data(payload)
        assert data["temp_tx1_D1"] == 62.7
        assert data["data_structure_type_tx1_D1"] == 1
        assert data["rainfall_daily_tx1_D1"] == pytest.approx(0.05)

        # AirLink reports "no error" as 0 instead of null
        payload["error"] = 0
        assert self.davis.parse_weather_data(payload)["temp_tx1_D1"] == 62.7


def test_migrate_unique_id():
    from custom_components.davis_weatherlink_live import migrate_unique_id

    assert migrate_unique_id("temp_tx1", "D1") == "temp_tx1_D1"
    assert migrate_unique_id("temp_tx1_D1", "D1") is None  # already migrated
    assert migrate_unique_id("bar_sea_level_ls309780", "D1") is None
    assert migrate_unique_id("pm_1_ls0ABC", "D1") is None


class FakeRegistry:
    """Minimal stand-in for HA's entity registry: {entity_id: unique_id}."""

    def __init__(self, entities):
        self.entities = dict(entities)

    def async_get_entity_id(self, domain, platform, unique_id):
        return next((e for e, u in self.entities.items() if u == unique_id), None)

    def async_remove(self, entity_id):
        del self.entities[entity_id]

    def async_update_entity(self, entity_id, new_unique_id):
        assert self.async_get_entity_id("sensor", None, new_unique_id) is None, "unique id in use"
        self.entities[entity_id] = new_unique_id


def run_migration(registry):
    from types import SimpleNamespace
    from unittest.mock import patch

    from custom_components.davis_weatherlink_live import er, migrate_entities

    entries = [SimpleNamespace(entity_id=e, unique_id=u, domain="sensor") for e, u in registry.entities.items()]
    with patch.object(er, "async_entries_for_config_entry", return_value=entries):
        migrate_entities(registry, "entry1", "D1")


def test_migrate_entities_renames_old_ids():
    registry = FakeRegistry({"sensor.iss_temp": "temp_tx1", "sensor.bar": "bar_sea_level_ls309780"})
    run_migration(registry)
    assert registry.entities == {"sensor.iss_temp": "temp_tx1_D1", "sensor.bar": "bar_sea_level_ls309780"}


def test_migrate_entities_cleans_up_duplicates():
    # State left by the dev build that skipped the migration: old entity + new "_2" duplicate
    registry = FakeRegistry({"sensor.iss_temp": "temp_tx1", "sensor.iss_temp_2": "temp_tx1_D1"})
    run_migration(registry)
    assert registry.entities == {"sensor.iss_temp": "temp_tx1_D1"}  # original entity (history) wins
