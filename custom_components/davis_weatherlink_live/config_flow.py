"""Setup config and options flow for Davis WeatherLink Live integration."""

from __future__ import annotations

import logging
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .const import API_INITIAL_INTERVAL, API_INITIAL_MAX_CACHE_AGE, API_PATH, DOMAIN

_LOGGER = logging.getLogger(__name__)


def _validate(user_input: dict[str, Any]) -> dict[str, str]:
    """Return form errors keyed by field."""
    errors: dict[str, str] = {}
    if "://" in user_input["api_host"]:  # a URL, not a host (allows e.g. weather-httpd.local)
        errors["api_host"] = "api_host_http_not_allowed"
    if user_input["update_interval"] < 10:
        errors["update_interval"] = "update_interval_too_low"
    return errors


def _build_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Form schema shared by the config and options flows, pre-filled from defaults."""
    cache = defaults.get("cache_section", {})
    return vol.Schema(
        {
            vol.Required("api_host", default=defaults.get("api_host", "")): cv.string,
            vol.Required("api_path", default=defaults.get("api_path", API_PATH)): cv.string,
            vol.Required(
                "update_interval",
                default=defaults.get("update_interval", API_INITIAL_INTERVAL),
            ): cv.positive_int,
            vol.Required("cache_section"): section(
                vol.Schema(
                    {
                        vol.Required("cache", default=cache.get("cache", False)): bool,
                        vol.Required(
                            "cache_age",
                            default=cache.get("cache_age", API_INITIAL_MAX_CACHE_AGE),
                        ): cv.positive_int,
                    }
                ),
                {"collapsed": True},
            ),
        }
    )


class WeatherStationConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Davis WeatherLink Live."""

    _discovered_host: str | None = None

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle a device found via zeroconf."""
        _LOGGER.debug("Zeroconf discovery_info: %s", discovery_info)

        # The device doesn't expose its serial via zeroconf, but the hostname
        # contains its last six digits, e.g. "weatherlinklive-33a9cb.local."
        await self.async_set_unique_id(discovery_info.hostname)
        self._abort_if_unique_id_configured()

        self._discovered_host = discovery_info.host
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the setup form."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._async_abort_entries_match({"api_host": user_input["api_host"]})
            errors = _validate(user_input)
            if not errors:
                return self.async_create_entry(
                    title="Davis Device",
                    data={},
                    options=user_input,  # options so they can be changed later
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(
                user_input or {"api_host": self._discovered_host or ""}
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> WeatherStationOptionsFlow:
        """Return the options flow."""
        return WeatherStationOptionsFlow()


class WeatherStationOptionsFlow(OptionsFlow):
    """Options flow for Davis WeatherLink Live."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the options form."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(user_input or dict(self.config_entry.options)),
            errors=errors,
        )
