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
            _LOGGER.info("Attempting BBC Sounds authentication for %s", username)
            await client.auth.authenticate(username=username, password=password)
            
            # Verify login state
            is_logged_in = client.auth.is_logged_in
            _LOGGER.info(
                "BBC Sounds authentication complete - logged_in: %s, user: %s",
                is_logged_in,
                username
            )
            
            # Try to get user info to verify the session
            try:
                await client.auth.set_user_info()
                is_uk = client.auth.is_uk_listener
                country = client.auth.listener_country
                _LOGGER.info(
                    "BBC user info - is_uk_listener: %s, country: %s",
                    is_uk,
                    country
                )
            except Exception as user_info_err:
                _LOGGER.warning("Could not fetch user info: %s", user_info_err)
                
        except exceptions.LoginFailedError as err:
            _LOGGER.error("BBC login failed: %s", err)
            raise ConfigEntryAuthFailed("Invalid BBC account credentials") from err
        except exceptions.NetworkError as err:
            _LOGGER.error("BBC network error: %s", err)
            raise ConfigEntryNotReady("Could not connect to BBC services") from err
        except exceptions.APIResponseError as err:
            _LOGGER.error("BBC API error: %s", err)
            raise ConfigEntryNotReady(f"BBC API error: {err}") from err
    else:
        _LOGGER.info("BBC Sounds configured without credentials (anonymous access)")
    
    # Store client in runtime_data for media_source to access
    entry.runtime_data = client
    
    # No platform forwarding needed - media_source registers itself via async_get_media_source
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BBCSoundsConfigEntry) -> bool:
    """Unload a config entry."""
    # Simple cleanup - no platforms to unload
    return True
