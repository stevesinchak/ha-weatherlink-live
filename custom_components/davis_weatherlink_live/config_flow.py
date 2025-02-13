from __future__ import annotations

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    OptionsFlowWithConfigEntry,
)

from typing import Any

from homeassistant.core import callback
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import logging
from .const import DOMAIN, API_PATH, API_INITIAL_INTERVAL

_LOGGER = logging.getLogger(__name__)

class WeatherStationConfigFlow(ConfigFlow, domain=DOMAIN):

    async def async_step_zeroconf(self, discovery_info):
        _LOGGER.info("Zeroconf discovery_info: %s", discovery_info)

        host = discovery_info.host

        # The WeatherLink Live device does not expose its serial number directly via Zeroconf.
        # Therefore, we must use the hostname which includes the last six digits of the serial number for a unique id. 
        # Example hostname: "weatherlinklive-33a9cb.local."
        unique_id = discovery_info.hostname
        _LOGGER.info("Discovered unique id: %s", unique_id)

        # Set unique_id and abort if it was set by Zeroconf to avoid duplicate device discovery
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()
        
        return await self._async_set_host(host)
    
    async def _async_set_host(self, host):
        self.context["host"] = host
        _LOGGER.info("Host set to: %s", host)
        return await self.async_step_user()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(
                title="Weather Station",
                data={},  # Store any required data here
                options=user_input  # Store user input in options so they can change them later
            )
        
        data_schema = vol.Schema({
            vol.Required("api_host", default=self.context.get("host", "")): cv.string, # Grab host from Zeroconf if available
            vol.Required("api_path", default=API_PATH): cv.string,
            vol.Required("update_interval", default=API_INITIAL_INTERVAL): cv.positive_int
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "api_host": "The hostname or IP address of the WeatherLink Live device.",
                "api_path": "The API path for accessing the WeatherLink Live data.",
                "update_interval": "The interval (in seconds) at which data should be updated."
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return WeatherStationOptionsFlow(config_entry)

class WeatherStationOptionsFlow(OptionsFlowWithConfigEntry):

    #def __init__(self, config_entry):

    async def async_step_init(self, user_input=None):
        errors = {}

        if user_input is not None:
            # Update options with new values
            return self.async_create_entry(title="", data=user_input)

        # Pre-fill form fields with current options
        data_schema = vol.Schema({
            vol.Required("api_host", default=self.config_entry.options.get("api_host", "")): cv.string,
            vol.Required("api_path", default=self.config_entry.options.get("api_path", "")): cv.string,
            vol.Required("update_interval", default=self.config_entry.options.get("update_interval", API_INITIAL_INTERVAL)): cv.positive_int,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "api_host": "The hostname or IP address of the WeatherLink Live device.",
                "api_path": "The API path for accessing the WeatherLink Live data.",
                "update_interval": "The interval (in seconds) at which data should be updated."
            }
        )