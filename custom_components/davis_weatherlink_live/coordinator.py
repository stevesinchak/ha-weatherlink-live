"""DataUpdateCoordinator for Davis WeatherLink Live integration."""

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import DOMAIN, HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .davis_weatherlink_live import DavisWeatherLinkLive

_LOGGER = logging.getLogger(__name__)


class WeatherCoordinator(DataUpdateCoordinator):
    """My example coordinator."""

    data: list[dict[str, Any]]

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
            data = await self.wll_local.get_weather_data()

        except Exception as err:
            # This will show entities as unavailable by raising UpdateFailed exception
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        # What is returned here is stored in self.data by the DataUpdateCoordinator
        return data