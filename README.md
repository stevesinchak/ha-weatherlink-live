# Davis WeatherLink Live Custom Integration
* [Introduction](#introduction)
* [Installation](#installation)
* [Configuration](#configuration)
* [Removal](#removal)
* [Troubleshooting](#troubleshooting)
* [Known Limitations](#known-limitations)

## Introduction

This custom integration for [Home Assistant](https://www.home-assistant.io/) provides direct local access to the [Davis WeatherLink Live](https://www.davisinstruments.com/products/weatherlink-live) device on your home network for cloud-free access to all of your weather station sensors.

The integration polls the [local API](https://weatherlink.github.io/weatherlink-live-local-api/) on the [Davis WeatherLink Live](https://www.davisinstruments.com/products/weatherlink-live) (at a user configurable interval) and exposes 43 sensors to Home Assistant for use on dashboards and automations: 

| Standard               | Rain                   | Wind                                |
|------------------------|------------------------|-------------------------------------|
| Temperature            | Rain Rate Latest       | Bar Absolute Pressure               |
| Humidity               | Rain Rate Last 15 Min  | Bar Sea Level Pressure              |
| Dew Point              | Rain Rate High         | Bar Trend Pressure                  |
| THW Index              | Rainfall Storm         | Wind Speed Avg Last 10 Min          |
| Wet Bulb               | Rain Storm At          | Wind Direction                      |
| Bar Absolute Pressure  | Rain Storm Start       | Wind Direction Rose                 |
| Bar Sea Level Pressure | Rain Storm End         | Wind Direction Avg Last Min         |
| Bar Trend Pressure     | Rainfall Last 15 Min   | Wind Direction Avg Last 2 Min       |
| Indoor Temperature     | Rainfall Last 24 Hours | Wind Direction Avg Last 10 Min      |
| Indoor Humidity        | Rainfall Last Hour     | Wind Direction Avg Last 10 Min Rose |
| Indoor Heat Index      | Rainfall Last Storm    | Wind Gust Last 2 Min                |
| Indoor Dew Point       | Rainfall Day           | Wind Gust Direction Last 2 Min      |
| ISS Battery Low        | Rainfall Month         | Wind Gust Last 10 Min               |
| ISS RX Status          | Rainfall Year          | Wind Gust Direction Last 10 Min     |
|                        | Rain Cup Size          |                                     |

## Installation

**Install Option A:**

1. Copy the entire `davis_weatherlink_live` directory from this repository into the `custom_components` directory on your Home Assistant installation. `custom_components` is nested within the base Home Assistant `config` directory, if it does not exist, you can create it. Tip: Use the [Studio Code Server](https://github.com/hassio-addons/addon-vscode/blob/main/vscode/DOCS.md) add-on for an easy way to navigate the file system and upload files.

2. Restart Home Assistant so the custom integration is recognized. 

3. There are two methods to add/enable the integration: 

    * Auto Discovery: If the WeatherLink Live is on the same network as your Home Assistant Server, the device should be auto-detected (thanks to Zeroconf) within a few minutes and will be listed under the Discoverd section. Go to your [Home Assistant Integrations dashboard](https://my.home-assistant.io/redirect/integrations/) and hit the Add button and jump to step 4. 

    * Manual Add: Click this link to manually add the integration.  

4. Depending on how the integration was added in the previous step, all fields may be pre-populated.  There are three fields total:

    * API Host: The ip address or hostname of your Davis WeatherLink Live

    * API Path: Path to the API Endpoint (leave at the default unless this changes in a future device firmware update)

    * Update Interval: How frequently you want the integration to capture new data measured in seconds.  I set mine to 10 seconds as I like to capture detailed wind data. In other cases a simple 5 minute interval, 300 seconds, is sufficient. **Note:** *The Davis WeatherLink Live only updates the API every 10 seconds so intervals lower than 10 may result in errors and/or duplicate data.*

**Install Option B:**

*Install via HACS (Coming Soon)*


## Configuration

At any point you can update the configuration you specified while adding the integration by simply going to the [Davis WeatherLink Live 6100](https://my.home-assistant.io/redirect/integration/?domain=davis_weatherlink_live) page and hitting the `CONFIGURE` button. This is helpful if you would like to adjust the Update Interval.  

## Removal

The integration can be uninstalled and removed with three steps:

1. Go to the [Davis WeatherLink Live 6100](https://my.home-assistant.io/redirect/integration/?domain=davis_weatherlink_live) integration page, click on the three dots to the right of the `CONFIGURE` button and select `Delete`. Hit `DELETE` again on the confirmation screen. The device and sensor entities have been deleted and the integration is no longer active. 

2. Delete the entire `davis_weatherlink_live` directory from the `custom_components` directory on to completely remove the inactive integration from your system. 

3. Reboot Home Assistant. 

## Troubleshooting

The most common issue with this integration is 

In the event you are experiencing a problem with this integration, please make sure you have entered the correct API host. It should contain an IP address or a hostname and nothing more (no http:// in front).

On the [Davis WeatherLink Live 6100](https://my.home-assistant.io/redirect/integration/?domain=davis_weatherlink_live) integration page you can also enable debug logging so all logs show up in your [Home Assistant Core logging page](https://my.home-assistant.io/redirect/logs/?).  

If you continue to have an issue, please open an issue [here](https://github.com/stevesinchak/ha-weatherlink-live/issues). 

## Known Limitations

This integrations fully supports all capabilities of the Davis WeatherLink Live 6100 but only for one weather station.  In the rare even you have multiple weather stations connected to WeatherLink Live, only the first weather station will be supported. If you would like this integration to support multiple weather stations, please open an issue [here](https://github.com/stevesinchak/ha-weatherlink-live/issues). 


### Home Assistant Integration Quality Scale Report

#### Bronze
- [x] `action-setup` - Service actions are registered in async_setup
- [x] `appropriate-polling` - If it's a polling integration, set an appropriate polling interval
- [ ] `brands` - Has branding assets available for the integration
- [x] `common-modules` - Place common patterns in common modules
- [ ] `config-flow-test-coverage` - Full test coverage for the config flow
- [x] `config-flow` - Integration needs to be able to be set up via the UI
    - [x] Uses `data_description` to give context to fields
    - [x] Uses `ConfigEntry.data` and `ConfigEntry.options` correctly
- [x] `dependency-transparency` - Dependency transparency
- [x] `docs-actions` - The documentation describes the provided service actions that can be used
- [x] `docs-high-level-description` - The documentation includes a high-level description of the integration brand, product, or service
- [x] `docs-installation-instructions` - The documentation provides step-by-step installation instructions for the integration, including, if needed, prerequisites
- [x] `docs-removal-instructions` - The documentation provides removal instructions
- [x] `entity-event-setup` - Entities event setup
- [x] `entity-unique-id` - Entities have a unique ID
- [x] `has-entity-name` - Entities use has_entity_name = True
- [ ] `runtime-data` - Use ConfigEntry.runtime_data to store runtime data
- [ ] `test-before-configure` - Test a connection in the config flow
- [ ] `test-before-setup` - Check during integration initialization if we are able to set it up correctly
- [x] `unique-config-entry` - Don't allow the same device or service to be able to be set up twice

#### Silver
- [ ] `action-exceptions` - Service actions raise exceptions when encountering failures
- [ ] `config-entry-unloading` - Support config entry unloading
- [x] `docs-configuration-parameters` - The documentation describes all integration configuration options
- [x] `docs-installation-parameters` - The documentation describes all integration installation parameters
- [ ] `entity-unavailable` - Mark entity unavailable if appropriate
- [x] `integration-owner` - Has an integration owner
- [ ] `log-when-unavailable` - If internet/device/service is unavailable, log once when unavailable and once when back connected
- [ ] `parallel-updates` - Set Parallel updates
- [n/a] `reauthentication-flow` - Reauthentication flow
- [ ] `test-coverage` - Above 95% test coverage for all integration modules

#### Gold
- [x] `devices` - The integration creates devices
- [ ] `diagnostics` - Implements diagnostics
- [x] `discovery-update-info` - Integration uses discovery info to update network information
- [x] `discovery` - Can be discovered
- [x] `docs-data-update` - The documentation describes how data is updated
- [ ] `docs-examples` - The documentation provides automation examples the user can use.
- [x] `docs-known-limitations` - The documentation describes known limitations of the integration (not to be confused with bugs)
- [x] `docs-supported-devices` - The documentation describes known supported / unsupported devices
- [x] `docs-supported-functions` - The documentation describes the supported functionality, including entities, and platforms
- [x] `docs-troubleshooting` - The documentation provides troubleshooting information
- [x] `docs-use-cases` - The documentation describes use cases to illustrate how this integration can be used
- [n/a] `dynamic-devices` - Devices added after integration setup
- [x] `entity-category` - Entities are assigned an appropriate EntityCategory
- [x] `entity-device-class` - Entities use device classes where possible
- [x] `entity-disabled-by-default` - Integration disables less popular (or noisy) entities
- [ ] `entity-translations` - Entities have translated names
- [ ] `exception-translations` - Exception messages are translatable
- [ ] `icon-translations` - Icon translations
- [x] `reconfiguration-flow` - Integrations should have a reconfigure flow
- [ ] `repair-issues` - Repair issues and repair flows are used when user intervention is needed
- [n/a] `stale-devices` - Clean up stale devices

#### Platinum
- [ ] `async-dependency` - Dependency is async
- [ ] `inject-websession` - The integration dependency supports passing in a websession
- [ ] `strict-typing` - Strict typing
