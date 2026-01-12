"""The BBC Sounds integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

try:
    from .sounds import SoundsClient, exceptions
    import pytz
except Exception:
    _LOGGER.exception("Failed to import sounds library")
    # Re-raise so HA knows it failed
    raise

from .const import DOMAIN
from .views import BBCSoundsLogoView

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.MEDIA_SOURCE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BBC Sounds from a config entry."""
    try:
        hass.data.setdefault(DOMAIN, {})

        # Register the logo view
        hass.http.register_view(BBCSoundsLogoView(hass))

        session = async_get_clientsession(hass)
        
        # Initialize SoundsClient
        # Use HA configured timezone or fallback to UTC
        tz_name = hass.config.time_zone or "UTC"
        try:
            timezone = pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            _LOGGER.warning("Unknown timezone %s, falling back to UTC", tz_name)
            timezone = pytz.UTC
        except Exception as err:
            _LOGGER.warning("Error getting timezone %s: %s, falling back to UTC", tz_name, err)
            timezone = pytz.UTC

        _LOGGER.debug("Initializing BBC Sounds client with timezone: %s", timezone)

        try:
            client = SoundsClient(
                session=session,
                logger=_LOGGER,
                timezone=timezone, 
            )
        except Exception as err:
            _LOGGER.error("Failed to initialize SoundsClient: %s", err)
            return False

        username = entry.data.get(CONF_USERNAME)
        password = entry.data.get(CONF_PASSWORD)

        if username and password:
            try:
                await client.auth.authenticate(username, password)
                _LOGGER.debug("Authenticated with BBC Sounds as %s", username)
            except exceptions.LoginFailedError as err:
                _LOGGER.error("Failed to authenticate with BBC Sounds: %s", err)
                return False
            except Exception as err:
                _LOGGER.error("Error during BBC Sounds authentication: %s", err)
                return False

        hass.data[DOMAIN][entry.entry_id] = client

        # We don't have traditional platforms yet, but we will ensure the component is loaded.
        # If we add media_player later, we add it here.
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        return True
    except Exception:
        raise


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(hass, entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
