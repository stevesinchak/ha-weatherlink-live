import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.davis_weatherlink_live import coordinator as coord_mod


def make_coordinator(cache: bool, cache_age: int = 60):
    entry = MagicMock()
    entry.entry_id = "entry1"
    entry.options = {
        "api_host": "1.2.3.4",
        "api_path": "/v1/current_conditions",
        "update_interval": 30,
        "cache_section": {"cache": cache, "cache_age": cache_age},
    }
    with patch.object(coord_mod, "async_get_clientsession"), patch.object(
        coord_mod.DataUpdateCoordinator, "__init__", return_value=None
    ):
        c = coord_mod.WeatherCoordinator(MagicMock(), entry)
    c.data = None
    c.wll_local = MagicMock()
    return c


def run(c):
    return asyncio.run(c._async_update_data())


def test_success_returns_new_data():
    c = make_coordinator(cache=False)
    c.wll_local.get_weather_data = AsyncMock(return_value={"temp_tx1": 1})
    assert run(c) == {"temp_tx1": 1}


def test_failure_without_cache_raises():
    c = make_coordinator(cache=False)
    c.data = {"temp_tx1": 1}
    c._last_success = coord_mod.time.monotonic()
    c.wll_local.get_weather_data = AsyncMock(side_effect=TimeoutError)
    with pytest.raises(UpdateFailed):
        run(c)


def test_failure_with_fresh_cache_returns_cached():
    c = make_coordinator(cache=True, cache_age=60)
    c.data = {"temp_tx1": 1}
    c._last_success = coord_mod.time.monotonic()
    c.wll_local.get_weather_data = AsyncMock(side_effect=TimeoutError)
    assert run(c) == {"temp_tx1": 1}


def test_failure_with_expired_cache_raises():
    c = make_coordinator(cache=True, cache_age=60)
    c.data = {"temp_tx1": 1}
    c._last_success = coord_mod.time.monotonic() - 61
    c.wll_local.get_weather_data = AsyncMock(side_effect=TimeoutError)
    with pytest.raises(UpdateFailed):
        run(c)


def test_first_refresh_failure_with_cache_raises():
    c = make_coordinator(cache=True)
    c.wll_local.get_weather_data = AsyncMock(side_effect=TimeoutError)
    with pytest.raises(UpdateFailed):
        run(c)
