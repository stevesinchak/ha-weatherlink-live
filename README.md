![Davis Logo](https://raw.githubusercontent.com/stevesinchak/ha-weatherlink-live/main/brand/davis_weatherlink_live/logo.png)

# Davis WeatherLink Live / AirLink Custom Integration
* [Introduction](#introduction)
* [Installation](#installation)
* [Configuration](#configuration)
* [Optional Advanced Data Caching](#optional-advanced-data-caching)
* [Optional Real-Time Wind & Rain](#optional-real-time-wind--rain)
* [Automation Examples](#automation-examples)
* [Known Limitations](#known-limitations)
* [Removal](#removal)
* [Troubleshooting](#troubleshooting)
* [Testing](#testing)

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

> **Requires Home Assistant 2026.7.0 or newer.** On older versions the integration will fail to load.

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

At any point, you can update the configuration you specified while adding the integration by simply going to the [Davis WeatherLink Live 6100](https://my.home-assistant.io/redirect/integration/?domain=davis_weatherlink_live) page and hitting the :gear: `Gear` button. This is helpful if you would like to adjust the Update Interval. The same screen also has two optional features, described below: Advanced Data Caching and Real-Time Wind & Rain.

If the device moves to a new IP address or hostname, you can also use the entry's ⋮ menu > `Reconfigure`. It only asks for the host and path, and checks that the new address is the same Davis device, so your sensors and history stay attached.

## Optional Advanced Data Caching

This feature is helpful if your Home Assistant server and WeatherLink Live have unreliable connectivity or if the Davis device is busy (multiple clients are accessing the API at the same time). The Davis hardware is designed to respond to one request at a time and does not support queuing of requests. If a new API request is received while it is still processing a previous request, the new request will automatically have its connection terminated. That will result in Home Assistant marking the sensors as "unavailable" until the next successful API response.

When caching is enabled, if the API is unreachable, the integration will reuse the last successful API response to populate sensor values until the cache expires. This prevents sensors from going to an "unavailable" state during short outages or device busy scenarios. You can set the cache expiration time (in seconds) to control how long cached data is used before giving up and marking sensors as unavailable. A reasonable cache expiration value is between 10 and 60 seconds to balance data freshness with reliability.

If you would like to use this feature, go to the [Davis WeatherLink Live](https://my.home-assistant.io/redirect/integration/?domain=davis_weatherlink_live) integration page, hit the :gear: `Gear` button, and expand the `Optional: Advanced Data Caching` section. Check the box to enable caching and set the cache expiration time. Hit `SUBMIT` to save your changes.

## Optional Real-Time Wind & Rain

The WeatherLink Live can broadcast wind and rain data on your local network every 2.5 seconds using its [real-time UDP broadcast](https://weatherlink.github.io/weatherlink-live-local-api/). When this option is enabled, the integration listens for those broadcasts and updates the wind and rain sensors of each ISS (wind speed, direction, gusts, rain rate, and rainfall totals) as soon as new data arrives. All other sensors (temperature, humidity, barometer, soil, AirLink, etc.) keep updating at your configured polling Update Interval.

This feature is off by default and fully separate from normal polling. If the broadcast can't be started or stops arriving, the wind and rain sensors simply fall back to the polled values within about 10 seconds.

**Requirements**

* A Davis WeatherLink Live with at least one ISS transmitter (the AirLink does not support real-time broadcasts).
* Home Assistant must be on the same local network (subnet/VLAN) as the WeatherLink Live. Broadcasts do not cross routers.
* Home Assistant must be able to receive UDP traffic on port 22222. If you run Home Assistant in Docker, use host networking. Home Assistant OS works out of the box.

**Enabling**

Go to the [Davis WeatherLink Live](https://my.home-assistant.io/redirect/integration/?domain=davis_weatherlink_live) integration page, hit the :gear: `Gear` button, and expand the `Optional: Real-Time Wind & Rain (WeatherLink Live only)` section. Check the box and hit `SUBMIT`. The integration reloads and requests the broadcast a few seconds later. It renews the request every minute, so the broadcast resumes on its own after a WeatherLink Live restart.

**Checking that it works**

Open a wind sensor's history: with real-time working, it updates every few seconds whenever the wind changes, instead of only at your Update Interval. If Home Assistant receives no broadcast packets in the first minute, a warning is written to the [Home Assistant logs](https://my.home-assistant.io/redirect/logs/?) with tips to check your network. For more detail, enable debug logging on the integration page (see [Troubleshooting](#troubleshooting)).

**Note:** *Real-time updates write wind and rain values to the Home Assistant database far more often than polling does (values are only written when they change, but wind changes often). If database size is a concern, consider excluding the fast-changing wind sensors from the [recorder](https://www.home-assistant.io/integrations/recorder/).*

## Automation Examples

Paste these into **Settings → Automations & scenes → Create automation → Edit in YAML**. The entity IDs are the defaults for ISS transmitter 1 and an AirLink; check yours under **Settings → Devices & services → Davis WeatherLink Live / AirLink** and adjust if they differ. Replace `cover.awning` and `fan.air_purifier` with your own devices.

**Notify when it starts raining**
```yaml
alias: "Rain started"
triggers:
  - trigger: numeric_state
    entity_id: sensor.davis_iss_tx_1_rain_rate_latest
    above: 0
actions:
  - action: notify.notify
    data:
      message: "It's raining ({{ states('sensor.davis_iss_tx_1_rain_rate_latest') }} in/h)"
```

**Close the awning in high wind** (with real-time mode on, this reacts within a few seconds)
```yaml
alias: "High wind: close awning"
triggers:
  - trigger: numeric_state
    entity_id: sensor.davis_iss_tx_1_wind_gust_last_10_min
    above: 30
actions:
  - action: cover.close_cover
    target:
      entity_id: cover.awning
  - action: notify.notify
    data:
      message: "Wind gust {{ states('sensor.davis_iss_tx_1_wind_gust_last_10_min') }} mph, closing the awning"
```

**Warn when the ISS battery is low**
```yaml
alias: "ISS battery low"
triggers:
  - trigger: state
    entity_id: sensor.davis_iss_tx_1_iss_battery_low
    to: "Yes"
actions:
  - action: notify.notify
    data:
      message: "The Davis ISS transmitter battery is low"
```

**Run the air purifier when air quality is poor**
```yaml
alias: "Poor air quality: purifier on"
triggers:
  - trigger: numeric_state
    entity_id: sensor.davis_airlink_aqm_current_pm2_5
    above: 35
    for:
      minutes: 10
actions:
  - action: fan.turn_on
    target:
      entity_id: fan.air_purifier
```

## Known Limitations

* **One request at a time:** The WeatherLink Live only answers one request at a time. If another app (or a second Home Assistant instance) also polls the same device, some updates may fail or the setup may show "Can't reach the device". Try again, or reduce how often the other app polls.
* **Real-time updates are wind and rain only:** The optional real-time mode covers only the ISS wind and rain sensors (not AirLink or other sensors). Home Assistant must be on the same local network as the WeatherLink Live to receive the UDP broadcast on port 22222 (Docker needs host networking).
* **Minimum update interval:** The polling interval can't be lower than 10 seconds, and values are only as fresh as the WeatherLink Live's own readings.
* **Home Assistant version:** Requires Home Assistant 2026.7.0 or newer.

## Removal

The integration can be uninstalled and removed with three steps:

1. Go to the [Davis WeatherLink Live 6100](https://my.home-assistant.io/redirect/integration/?domain=davis_weatherlink_live) integration page, click on the three dots to the right of the :gear: `Gear` button, and select `Delete`. Hit `DELETE` again on the confirmation screen. The device and sensor entities have been deleted, and the integration is no longer active. 

2. Delete the entire `davis_weatherlink_live` directory from the `custom_components` directory on to completely remove the inactive integration from your system. 

3. Reboot Home Assistant. 

## Troubleshooting

In the event you are experiencing a problem with this integration, please make sure you have entered the correct API host. It should contain an IP address or a hostname and nothing more (no http:// in front).

On the [Davis WeatherLink Live 6100](https://my.home-assistant.io/redirect/integration/?domain=davis_weatherlink_live) integration page, you can also enable debug logging so all logs show up in your [Home Assistant Core logging page](https://my.home-assistant.io/redirect/logs/?). 

If you continue to have an issue, please open an issue [here](https://github.com/stevesinchak/ha-weatherlink-live/issues) and provide copies of logs with debug enabled. You can also download diagnostics from the integration's ⋮ menu and attach the file to your issue (your IP address is removed).

## Testing

The integration has **75 automated tests** with **100% code coverage** (every line of every module runs during the tests). They run against the oldest supported Home Assistant (2026.7) and the newest release.

| Module | Coverage |
|---|---|
| `__init__.py` (setup, unload, migrations) | 100% |
| `config_flow.py` (setup, discovery, reconfigure, options) | 100% |
| `const.py` | 100% |
| `coordinator.py` (polling and cache) | 100% |
| `davis_weatherlink_live.py` (API client and unit conversion) | 100% |
| `diagnostics.py` | 100% |
| `realtime.py` (UDP wind and rain) | 100% |
| `sensor.py` | 100% |

What the tests cover:

| Test file | Tests | What it checks |
|---|---|---|
| `test_config_flow.py` | 20 | Adding the integration, field validation, connection errors, duplicate devices, zeroconf discovery (including a device moving to a new IP), Reconfigure, and the options screen |
| `test_davis_weather_link_live.py` | 16 | The API client and helpers: timestamps (including bad ones), battery status, wind direction, rain unit conversion, rejecting bad device data, unique ID migration from older versions, and removing stale devices |
| `test_realtime.py` | 13 | Real-time UDP: parsing broadcasts, renewing the broadcast request, and falling back to polling when it fails |
| `test_init.py` | 11 | Setting up the whole integration with simulated device data: sensors and devices created, hub naming, setup retries, old Home Assistant versions, new transmitters added later |
| `test_coordinator.py` | 6 | Polling, the optional cache during outages, and logging when the device goes offline and comes back |
| `test_fake_apis.py` | 6 | The bundled device simulators (`fake_api*.py`) return data for every sensor, sensor IDs never collide, and a refused connection raises an error |
| `test_diagnostics.py` | 2 | Diagnostics download, with the IP address removed |
| `test_typing.py` | 1 | The code passes `mypy --strict` type checking |

To run them yourself (Python 3.14):

```bash
pip install -r requirements.txt
pytest --cov=custom_components.davis_weatherlink_live --cov-report=term-missing
```

## Project Support

If you are a happy user and would like to support the project, please contribute to the project by opening an issue, enhancement request, start a discussion, or submit a pull request to make it better. Thank you -Steve

## Home Assistant Integration Quality Scale Report

This integration meets the **Platinum** tier: every rule below is done or exempt (exempt rules give the reason). The same status is tracked in [quality_scale.yaml](custom_components/davis_weatherlink_live/quality_scale.yaml).

### Bronze
- (N/A no service actions) `action-setup` - Service actions are registered in async_setup
- [x] `appropriate-polling` - If it's a polling integration, set an appropriate polling interval
- [x] `brands` - Has branding assets available for the integration
- [x] `common-modules` - Place common patterns in common modules
- [x] `config-flow-test-coverage` - Full test coverage for the config flow
- [x] `config-flow` - Integration needs to be able to be set up via the UI
    - [x] Uses `data_description` to give context to fields
    - [x] Uses `ConfigEntry.data` and `ConfigEntry.options` correctly
- [x] `dependency-transparency` - Dependency transparency
- (N/A no service actions) `docs-actions` - The documentation describes the provided service actions that can be used
- [x] `docs-high-level-description` - The documentation includes a high-level description of the integration brand, product, or service
- [x] `docs-installation-instructions` - The documentation provides step-by-step installation instructions for the integration, including, if needed, prerequisites
- [x] `docs-removal-instructions` - The documentation provides removal instructions
- [x] `entity-event-setup` - Entities event setup
- [x] `entity-unique-id` - Entities have a unique ID
- [x] `has-entity-name` - Entities use has_entity_name = True
- [x] `runtime-data` - Use ConfigEntry.runtime_data to store runtime data
- [x] `test-before-configure` - Test a connection in the config flow
- [x] `test-before-setup` - Check during integration initialization if we are able to set it up correctly
- [x] `unique-config-entry` - Don't allow the same device or service to be able to be set up twice

### Silver
- (N/A no service actions) `action-exceptions` - Service actions raise exceptions when encountering failures
- [x] `config-entry-unloading` - Support config entry unloading
- [x] `docs-configuration-parameters` - The documentation describes all integration configuration options
- [x] `docs-installation-parameters` - The documentation describes all integration installation parameters
- [x] `entity-unavailable` - Mark entity unavailable if appropriate
- [x] `integration-owner` - Has an integration owner
- [x] `log-when-unavailable` - If internet/device/service is unavailable, log once when unavailable and once when back connected
- [x] `parallel-updates` - Set Parallel updates
- (N/A no auth) `reauthentication-flow` - Reauthentication flow
- [x] `test-coverage` - Above 95% test coverage for all integration modules

### Gold
- [x] `devices` - The integration creates devices
- [x] `diagnostics` - Implements diagnostics
- [x] `discovery-update-info` - Integration uses discovery info to update network information
- [x] `discovery` - Can be discovered
- [x] `docs-data-update` - The documentation describes how data is updated
- [x] `docs-examples` - The documentation provides automation examples the user can use.
- [x] `docs-known-limitations` - The documentation describes known limitations of the integration (not to be confused with bugs)
- [x] `docs-supported-devices` - The documentation describes known supported / unsupported devices
- [x] `docs-supported-functions` - The documentation describes the supported functionality, including entities, and platforms
- [x] `docs-troubleshooting` - The documentation provides troubleshooting information
- [x] `docs-use-cases` - The documentation describes use cases to illustrate how this integration can be used
- [x] `dynamic-devices` - Devices added after integration setup
- [x] `entity-category` - Entities are assigned an appropriate EntityCategory
- [x] `entity-device-class` - Entities use device classes where possible
- [x] `entity-disabled-by-default` - Integration disables less popular (or noisy) entities
- [x] `entity-translations` - Entities have translated names
- [x] `exception-translations` - Exception messages are translatable
- [x] `icon-translations` - Icon translations
- [x] `reconfiguration-flow` - Integrations should have a reconfigure flow
- (N/A nothing to repair) `repair-issues` - Repair issues and repair flows are used when user intervention is needed
- [x] `stale-devices` - Clean up stale devices

### Platinum
- [x] `async-dependency` - Dependency is async
- [x] `inject-websession` - The integration dependency supports passing in a websession
- [x] `strict-typing` - Strict typing