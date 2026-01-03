"""DataUpdateCoordinator for Davis WeatherLink Live integration."""

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import DOMAIN, HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_INITIAL_MAX_CACHE_AGE
from .davis_weatherlink_live import DavisWeatherLinkLive

_LOGGER = logging.getLogger(__name__)


class WeatherCoordinator(DataUpdateCoordinator):
    """My example coordinator."""

    data: list[dict[str, Any]]

    # Track when we last had fresh data
    last_data_received_time = None

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""

        # Set variables from values entered in config flow and option flow setup
        self.api_host = config_entry.options.get(
            "api_host"
        )  # ,config_entry.data["api_host"])
        self.api_path = config_entry.options.get(
            "api_path"
        )  # ,config_entry.data["api_path"])
        self.api_update_interval = config_entry.options.get(
            "update_interval"
        )  # ,config_entry.data["update_interval"])
        self.api_cache = config_entry.options.get("cache_section", {}).get(
            "cache", False
        )
        self.api_cache_age = config_entry.options.get("cache_section", {}).get(
            "cache_age", API_INITIAL_MAX_CACHE_AGE
        )

        _LOGGER.debug("cache option: %s", self.api_cache)
        _LOGGER.debug("cache age: %s", self.api_cache_age)

        _LOGGER.debug("API Host: %s", self.api_host)
        _LOGGER.debug("API Path: %s", self.api_path)
        _LOGGER.debug("Update Interval: %s", self.api_update_interval)

        # Initialise DataUpdateCoordinator
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}",
            # Method to call on every update interval.
            update_method=self.async_update_data,
            # Polling interval. Will only be polled if you have made your
            # platform entities, CoordinatorEntities.
            # Using config option here but you can just use a fixed value.
            update_interval=timedelta(seconds=self.api_update_interval),
            # Set always_update to `False` if the data returned from the
            # api can be compared via `__eq__` to avoid duplicate updates
            # being dispatched to listeners
            always_update=False,
        )

        wll_url = "http://" + self.api_host + self.api_path
        _LOGGER.debug("WeatherLink Live URL %s", wll_url)

        # Create an instance of the API using the provided URL and pass in websession for API object to use
        self.wll_local = DavisWeatherLinkLive(
            wll_url, async_get_clientsession(hass)
        )  # @config_entry.runtime_data.websession)

        # Initialise your api here and make available to your integration.
        # self.api = API(host=self.host, user=self.user, pwd=self.pwd, mock=True)

    async def async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to retrieve and pre-process the data into an appropriate data structure
        to be used to provide values for all your entities.
        """
        _LOGGER.debug("Fetching data from API")
        try:
            # ----------------------------------------------------------------------------
            # Get the data from your api
            # ----------------------------------------------------------------------------

            # Old Requests based method
            # data = await self.hass.async_add_executor_job(self.wll_local.get_weather_data)

            # New injected websession based method
            new_data = await self.wll_local.get_weather_data()

            # Initialize data and last data timestamp if it's the first run
            if self.data is None:
                _LOGGER.debug("first run, initializing data store")
                self.data = {}
                self.last_data_received_time = datetime.min

            # Detect if we have full data or an error state
            _LOGGER.debug("Count of new API data: %d", len(new_data))
            _LOGGER.debug("Count of existing (cached) API data: %d", len(self.data))

            if len(new_data) > 0:
                # Update last_data_received_time to current datetime if we have real data
                self.last_data_received_time = datetime.now()

            # Depending if cache is enabled, expired, or disabled, return merged or new data
            if self.api_cache:
                _LOGGER.debug(
                    "Caching is enabled and expiration set to %d seconds",
                    self.api_cache_age,
                )

                # Check if cache is expired - expiration defined by self.api_cache_age via options/config flow
                time_since_last_data = datetime.now() - self.last_data_received_time
                _LOGGER.debug(
                    "Cached API data is %d second(s) old",
                    round(time_since_last_data.total_seconds()),
                )

                if (
                    round(time_since_last_data.total_seconds()) < 1
                    and len(new_data) > 0
                ):
                    _LOGGER.debug(
                        "API is working, returning latest data direct from API"
                    )
                    return new_data

                elif time_since_last_data > timedelta(seconds=self.api_cache_age):
                    _LOGGER.warning(
                        "No new API data received for %d seconds",
                        round(time_since_last_data.total_seconds()),
                    )
                    _LOGGER.warning(
                        "API still not responding and the Cache has expired! Time to shut this down to preserve the integrity of the sensors"
                    )
                    # return new_data
                    raise UpdateFailed(
                        "UpdateFailed - Error communicating with API and cache expired"
                    )

                else:
                    _LOGGER.warning(
                        "Using cached API data as the API is not responding and the cache has not yet expired"
                    )

                    # What is returned here is stored in self.data by the DataUpdateCoordinator
                    return self.data

            else:
                _LOGGER.debug(
                    "API is working, returning latest data direct from API. Cache is disabled."
                )

                # What is returned here is stored in self.data by the DataUpdateCoordinator
                return new_data

        except Exception as err:
            # This will show entities as unavailable by raising UpdateFailed exception
            raise UpdateFailed(
                f"UpdateFailed - Error communicating with API: {err}"
            ) from err

        # What is returned here is stored in self.data by the DataUpdateCoordinator
        # return data
