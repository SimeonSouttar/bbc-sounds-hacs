"""The BBC Sounds integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from sounds import SoundsClient, exceptions

from .const import DOMAIN

if TYPE_CHECKING:
    from aiohttp import ClientSession

_LOGGER = logging.getLogger(__name__)

# Type alias for config entry with runtime data
type BBCSoundsConfigEntry = ConfigEntry[SoundsClient]


async def async_setup_entry(hass: HomeAssistant, entry: BBCSoundsConfigEntry) -> bool:
    """Set up BBC Sounds from a config entry."""
    session: ClientSession = async_get_clientsession(hass)
    
    # Get timezone from HA config
    try:
        from zoneinfo import ZoneInfo
        timezone = ZoneInfo(hass.config.time_zone) if hass.config.time_zone else None
    except Exception:
        timezone = None
    
    client = SoundsClient(
        session=session,
        logger=_LOGGER,
        timezone=timezone,
    )
    
    # Authenticate if credentials are provided
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    
    if username and password:
        try:
            await client.auth.authenticate(username=username, password=password)
            _LOGGER.debug("Authenticated with BBC Sounds as %s", username)
        except exceptions.LoginFailedError as err:
            raise ConfigEntryAuthFailed("Invalid BBC account credentials") from err
        except exceptions.NetworkError as err:
            raise ConfigEntryNotReady("Could not connect to BBC services") from err
        except exceptions.APIResponseError as err:
            raise ConfigEntryNotReady(f"BBC API error: {err}") from err
    
    # Store client in runtime_data for media_source to access
    entry.runtime_data = client
    
    # No platform forwarding needed - media_source registers itself via async_get_media_source
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BBCSoundsConfigEntry) -> bool:
    """Unload a config entry."""
    # Simple cleanup - no platforms to unload
    return True
