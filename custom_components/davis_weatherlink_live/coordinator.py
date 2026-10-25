"""DataUpdateCoordinator for Davis WeatherLink Live integration."""

from __future__ import annotations

import logging
import time
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_INITIAL_MAX_CACHE_AGE, DOMAIN
from .davis_weatherlink_live import DavisWeatherLinkLive

_LOGGER = logging.getLogger(__name__)


class WeatherCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the WeatherLink Live / AirLink local API."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator from config entry options."""
        options = config_entry.options
        cache = options.get("cache_section", {})
        self.api_cache: bool = cache.get("cache", False)
        self.api_cache_age: int = cache.get("cache_age", API_INITIAL_MAX_CACHE_AGE)
        self._last_success: float | None = None

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=options["update_interval"]),
            always_update=False,
        )

        wll_url = f"http://{options['api_host']}{options['api_path']}"
        _LOGGER.debug(
            "URL %s, interval %ss, cache %s (%ss)",
            wll_url,
            options["update_interval"],
            self.api_cache,
            self.api_cache_age,
        )
        self.wll_local = DavisWeatherLinkLive(
            wll_url, async_get_clientsession(hass), config_entry.entry_id
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data, falling back to cached data for short outages if enabled."""
        try:
            data = await self.wll_local.get_weather_data()
        except Exception as err:
            if (
                self.api_cache
                and self.data
                and self._last_success is not None
                and time.monotonic() - self._last_success < self.api_cache_age
            ):
                _LOGGER.warning(
                    "Davis API not responding (%s), using cached data", err
                )
                return self.data
            raise UpdateFailed(f"Error communicating with Davis API: {err}") from err

        self._last_success = time.monotonic()
        return data
