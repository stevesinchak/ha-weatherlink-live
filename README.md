![Davis Logo](https://raw.githubusercontent.com/stevesinchak/ha-weatherlink-live/main/brand/davis_weatherlink_live/logo.png)

# Davis WeatherLink Live / AirLink Custom Integration
* [Introduction](#introduction)
* [Installation](#installation)
* [Configuration](#configuration)
* [Removal](#removal)
* [Troubleshooting](#troubleshooting)
* [Known Limitations](#known-limitations)

## Introduction

This custom integration for [Home Assistant](https://www.home-assistant.io/) provides direct local access to the [Davis WeatherLink Live 6100](https://www.davisinstruments.com/products/weatherlink-live) device on your home network for cloud-free access to all weather station sensors.

The integration polls the [local API](https://weatherlink.github.io/weatherlink-live-local-api/) on the [Davis WeatherLink Live](https://www.davisinstruments.com/products/weatherlink-live) (at a user-configurable interval). It exposes 50 sensors to Home Assistant for use on dashboards and automations (not all enabled by default): 

| Standard           | Rain                   | Wind                                | Pressure & Diagnostic  |
|--------------------|------------------------|-------------------------------------|------------------------|
| Temperature        | Rain Rate Latest       | Wind Speed                          | Bar Sea Level Pressure |
| Humidity           | Rain Rate High         | Wind Direction                      | Bar Trend Pressure     |
| Dew Point          | Rainfall Last 15 Min   | Wind Direction Rose                 | Bar Absolute Pressure  |
| Wet Bulb           | Rain Rate Last 15 Min  | Wind Speed Avg Last Min             | ISS Logical Sensor ID  |
| Heat Index         | Rainfall Last Hour     | Wind Direction Avg Last Min         | ISS Transmitter ID     |
| Wind Chill         | Rainfall Last 24 Hours | Wind Speed Avg Last 2 Min           | ISS RX Status          |
| THW Index          | Rainfall Storm         | Wind Direction Avg Last 2 Min       | ISS Battery Low        |
| THSW Index         | Rain Storm At          | Wind Gust Last 2 Min                | Rain Cup Size          |
| Solar Radiation    | Rainfall Day           | Wind Gust Direction Last 2 Min      |                        |
| UV Index           | Rainfall Month         | Wind Speed Avg Last 10 Min          |                        |
| Indoor Temperature | Rainfall Year          | Wind Direction Avg Last 10 Min      |                        |
| Indoor Humidity    | Rainfall Last Storm    | Wind Direction Avg Last 10 Min Rose |                        |
| Indoor Dew Point   | Rain Storm Start       | Wind Gust Last 10 Min               |                        |
| Indoor Heat Index  | Rain Storm End         | Wind Gust Direction Last 10 Min     |                        |

This integration also supports the [local api](https://weatherlink.github.io/airlink-local-api/) of the [Davis AirLink Air Quality Monitor](https://www.davisinstruments.com/pages/airlink) device with all 24 sensors. 

| Standard    | Particulate Matter | PM Averages         | Diagnostic              |
|-------------|--------------------|---------------------|-------------------------|
| Temperature | Current PM1        | PM1 Last Minute     | Last Report Time        |
| Humidity    | Current PM2.5      | PM2.5 Last Minute   | % PM Data Last Hour     |
| Dew Point   | Current PM10       | PM2.5 Last Hour     | % PM Data Last 3 Hours  |
| Wet Bulb    |                    | PM2.5 Last 3 Hours  | % PM Data Last 12 Hours |
| Heat Index  |                    | PM2.5 Last 12 Hours | % PM Data Last 24 Hours |
|             |                    | PM2.5 Last 24 Hours |                         |
|             |                    | PM10 Last Minute    |                         |
|             |                    | PM10 Last Hour      |                         |
|             |                    | PM10 Last 3 Hours   |                         |
|             |                    | PM10 Last 12 Hours  |                         |
|             |                    | PM10 Last 24 Hours  |                         |

## Installation

**Install with File Copy**

1. Copy the entire `davis_weatherlink_live` directory from this repository into the `custom_components` directory on your Home Assistant installation. `custom_components` is nested within the base Home Assistant `config` directory; if it does not exist, you can create it. Tip: Use the [Studio Code Server](https://github.com/hassio-addons/addon-vscode/blob/main/vscode/DOCS.md) add-on for an easy way to navigate the file system and upload files.

2. Restart Home Assistant so the custom integration is recognized. 

**Install with Home Assistant Community Store**

1. If you have HACS ([Home Assistant Community Store](https://www.hacs.xyz/)) installed on your Home Assistant server, you can add this repo as a Custom Repository. Simply click on the three dots in the top right of the Home Assistant Community Store page, and select `Custom repositories`.

2. Copy and paste the URL of this repository `https://github.com/stevesinchak/ha-weatherlink-live` and set the Type to `Integration` and hit Add. 

3. Then just search for `Davis WeatherLink Live` and click on the listing. Scroll down and hit Download to install. 

4. Reboot your Home Assistant server, and you are ready to configure.


## Configuration

1. There are two methods to add/enable the integration: 

    * Auto Discovery: If the WeatherLink Live is on the same network as your Home Assistant Server, the device should be auto-detected (thanks to Zeroconf) within a few minutes and will be listed under the Discovered section. Go to your [Home Assistant Integrations dashboard](https://my.home-assistant.io/redirect/integrations/) and hit the Add button, and jump to step 4. 

    * Manual Add: [Click this link to add the integration manually](https://my.home-assistant.io/redirect/config_flow_start/?domain=davis_weatherlink_live). 

2. Depending on how the integration was added in the previous step, all fields may be pre-populated, but are available to be adjusted. There are three fields total:

    * API Host: The ip address or hostname of your Davis WeatherLink Live

    * API Path: Path to the API Endpoint (leave at the default unless this changes in a future device firmware update)

    * Update Interval: How frequently you want the integration to capture new data, measured in seconds. I set mine to 10 seconds as I prefer to capture detailed wind data. In other cases, a simple 5-minute interval, 300 seconds, is sufficient. **Note:** *The Davis WeatherLink Live only updates the API every 10 seconds; intervals lower than 10 may result in errors and/or duplicate data, so the integration will not accept values below 10.*

    Hit `SUBMIT` when you are ready to proceed with setup.

3. The integration will automatically build a device in Home Assistant for each physical device registered on the Davis WeatherLink Live. This includes all potential sensors for the device type listed in the API specification (even if they are not present). On this final setup screen, you will have an opportunity to fine-tune the device names and set the 'Area' you want them to be assigned in Home Assistant. If you are happy with the defaults, hit `SKIP AND FINISH` to complete the setup.

**Note: You may want to disable specific device sensors that are not relevant for your device hardware. Unfortunately, the Davis WeatherLink Live API does not provide a good way for this integration to identify specific sensors that are not present, as the actual sensor device model sending the data to the WeatherLink Live is not available in the local API. I explored automatically disabling sensors that have null or zero values upon setup, but observed that this was not a reliable technique, as some sensors would send actual data later, or a zero value is legitimate in many cases (no wind). If anyone has a better approach, please [start a discussion here](https://github.com/stevesinchak/ha-weatherlink-live/discussions).**

At any point, you can update the configuration you specified while adding the integration by simply going to the [Davis WeatherLink Live 6100](https://my.home-assistant.io/redirect/integration/?domain=davis_weatherlink_live) page and hitting the :gear: `Gear` button. This is helpful if you would like to adjust the Update Interval. 

## Optional Advanced Data Caching

This feature is helpful if your Home Assistant server and WeatherLink Live have unreliable connectivity or if the Davis device is busy (multiple clients are accessing the API at the same time). The Davis hardware is designed to respond to one request at a time and does not support queuing of requests. If a new API request is received while it is still processing a previous request, the new request will automatically have its connection terminated. That will result in Home Assistant marking the sensors as "unavailable" until the next successful API response.

When caching is enabled, if the API is unreachable, the integration will reuse the last successful API response to populate sensor values until the cache expires. This prevents sensors from going to an "unavailable" state during short outages or device busy scenarios. You can set the cache expiration time (in seconds) to control how long cached data is used before giving up and marking sensors as unavailable. A reasonable cache expiration value is between 10 and 60 seconds to balance data freshness with reliability.

If you would like to use this feature, go to the [Davis WeatherLink Live](https://my.home-assistant.io/redirect/integration/?domain=davis_weatherlink_live) integration page, hit the :gear: `Gear` button, and expand the `Optional: Advanced Data Caching` section. Check the box to enable caching and set the cache expiration time. Hit `SUBMIT` to save your changes.

## Removal

The integration can be uninstalled and removed with three steps:

1. Go to the [Davis WeatherLink Live 6100](https://my.home-assistant.io/redirect/integration/?domain=davis_weatherlink_live) integration page, click on the three dots to the right of the :gear: `Gear` button, and select `Delete`. Hit `DELETE` again on the confirmation screen. The device and sensor entities have been deleted, and the integration is no longer active. 

2. Delete the entire `davis_weatherlink_live` directory from the `custom_components` directory on to completely remove the inactive integration from your system. 

3. Reboot Home Assistant. 

## Troubleshooting

In the event you are experiencing a problem with this integration, please make sure you have entered the correct API host. It should contain an IP address or a hostname and nothing more (no http:// in front).

On the [Davis WeatherLink Live 6100](https://my.home-assistant.io/redirect/integration/?domain=davis_weatherlink_live) integration page, you can also enable debug logging so all logs show up in your [Home Assistant Core logging page](https://my.home-assistant.io/redirect/logs/?). 

If you continue to have an issue, please open an issue [here](https://github.com/stevesinchak/ha-weatherlink-live/issues) and provide copies of logs with debug enabled. 

## Project Support

If you are a happy user and would like to support the project, please contribute to the project by opening an issue, enhancement request, start a discussion, or submit a pull request to make it better. Thank you -Steve

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
- [x] `config-entry-unloading` - Support config entry unloading
- [x] `docs-configuration-parameters` - The documentation describes all integration configuration options
- [x] `docs-installation-parameters` - The documentation describes all integration installation parameters
- [ ] `entity-unavailable` - Mark entity unavailable if appropriate
- [x] `integration-owner` - Has an integration owner
- [ ] `log-when-unavailable` - If internet/device/service is unavailable, log once when unavailable and once when back connected
- [ ] `parallel-updates` - Set Parallel updates
- (N/A no auth) `reauthentication-flow` - Reauthentication flow
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
- N/A `dynamic-devices` - Devices added after integration setup
- [x] `entity-category` - Entities are assigned an appropriate EntityCategory
- [x] `entity-device-class` - Entities use device classes where possible
- [x] `entity-disabled-by-default` - Integration disables less popular (or noisy) entities
- [x] `entity-translations` - Entities have translated names
- [ ] `exception-translations` - Exception messages are translatable
- [ ] `icon-translations` - Icon translations
- [x] `reconfiguration-flow` - Integrations should have a reconfigure flow
- [ ] `repair-issues` - Repair issues and repair flows are used when user intervention is needed
- N/A `stale-devices` - Clean up stale devices

#### Platinum
- [x] `async-dependency` - Dependency is async
- [x] `inject-websession` - The integration dependency supports passing in a websession
- [ ] `strict-typing` - Strict typing