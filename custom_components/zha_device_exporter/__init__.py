"""Custom component used to export ZHA Zigbee devices to a JSON file."""

import collections
import dataclasses
import logging
import os
from typing import Any
from copy import deepcopy

import voluptuous as vol
from homeassistant.components.zha.diagnostics import get_endpoint_cluster_attr_data
from homeassistant.components.zha.helpers import (
    ZHADeviceProxy,
    ZHAGatewayProxy,
    async_get_zha_device_proxy,
    get_zha_gateway_proxy,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.json import save_json
from slugify import slugify
from zigpy.quirks import CustomDevice
from zigpy.quirks.v2 import CustomDeviceV2

ATTR_OUTPUT_DIR = "output_dir"
DOMAIN = "zha_device_exporter"
CONFIG_OUTPUT_DIR_NAME = "zha-device-export"
SERVICE_EXPORT_DEVICES = "export_devices"
SERVICE_SCHEMAS = {SERVICE_EXPORT_DEVICES: vol.Schema({})}
ATTRIBUTES = "attributes"
CLUSTER_DETAILS = "cluster_details"
UNSUPPORTED_ATTRIBUTES = "unsupported_attributes"

LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Set up zha-device-exporter from config."""
    if DOMAIN not in config:
        return True

    output_dir = os.path.join(hass.config.config_dir, CONFIG_OUTPUT_DIR_NAME)

    def mkdir(directory):
        try:
            os.mkdir(directory)
            return True
        except OSError as exc:
            LOGGER.error("Couldn't create '%s' dir: %s", directory, exc)
            return False

    if not os.path.isdir(output_dir):
        if not await hass.async_add_executor_job(mkdir, output_dir):
            return False

    async def export_devices_handler(service) -> None:
        """Export ZHA device diagnostics files."""
        gateway_proxy: ZHAGatewayProxy = get_zha_gateway_proxy(hass)
        processed_devices: set[str] = set()  # used to avoid duplicate files
        for device in gateway_proxy.device_proxies.values():
            zha_device_proxy: ZHADeviceProxy = async_get_zha_device_proxy(
                hass, device.device_id
            )
            # slug for file name and deduplication
            manufacturer_model_slug = slugify(
                f"{zha_device_proxy.device.manufacturer}-{zha_device_proxy.device.model}"
            )

            # skip already processed devices
            if manufacturer_model_slug in processed_devices:
                continue

            processed_devices.add(manufacturer_model_slug)

            device_info: dict[str, Any] = zha_device_proxy.zha_device_info
            device_info[CLUSTER_DETAILS] = get_endpoint_cluster_attr_data(
                zha_device_proxy.device
            )

            original_signature = None
            if isinstance(zha_device_proxy.device.device, CustomDeviceV2):
                original_signature = deepcopy(
                    zha_device_proxy.device.device.replacement
                )
            elif isinstance(zha_device_proxy.device.device, CustomDevice):
                original_signature = deepcopy(zha_device_proxy.device.device.signature)

            # if we have a quirked device we add the original signature to the output and
            # convert the profile_id, device_type, input_clusters and output_clusters to hex
            # representation to make it consistent with the rest of the data
            if original_signature:
                for ep in original_signature["endpoints"].values():
                    if "profile_id" in ep:
                        ep["profile_id"] = f"0x{ep["profile_id"]:04x}"
                    if "device_type" in ep:
                        ep["device_type"] = f"0x{ep["device_type"]:04x}"
                    if "input_clusters" in ep:
                        ep["input_clusters"] = [
                            f"0x{c:04x}" for c in ep["input_clusters"]
                        ]
                    if "output_clusters" in ep:
                        ep["output_clusters"] = [
                            f"0x{c:04x}" for c in ep["output_clusters"]
                        ]
                device_info["original_signature"] = original_signature

            # add ZHA library entities
            platform_entities = collections.defaultdict(list)
            for (
                (platform, unique_id),
                platform_entity,
            ) in zha_device_proxy.device.platform_entities.items():
                lib_entity_info = {
                    "info_object": dataclasses.asdict(platform_entity.info_object),
                    "state": platform_entity.state,
                }
                for cluster_handler_info in lib_entity_info["info_object"][
                    "cluster_handlers"
                ]:
                    cluster_info = cluster_handler_info["cluster"]
                    if cluster_info is not None:
                        cluster_info.pop("commands", None)
                platform_entities[platform].append(lib_entity_info)
            device_info["zha_lib_entities"] = platform_entities

            file_name = os.path.join(
                output_dir,
                f"{manufacturer_model_slug}.json",
            )
            try:
                await hass.async_add_executor_job(save_json, file_name, device_info)
            except Exception as e:
                LOGGER.error("Couldn't save '%s' file: %s", file_name, e)

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_DEVICES,
        export_devices_handler,
        schema=SERVICE_SCHEMAS[SERVICE_EXPORT_DEVICES],
    )

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up ZHA.

    Will automatically load components to support devices found on the network.
    """

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload ZHA config entry."""

    return True
