"""Config flow for BBC Sounds integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from sounds import SoundsClient, exceptions

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_USERNAME): str,
        vol.Optional(CONF_PASSWORD): str,
    }
)


class BBCSoundsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BBC Sounds."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Only allow one instance
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            username = user_input.get(CONF_USERNAME)
            password = user_input.get(CONF_PASSWORD)

            # Validate credentials if provided
            if username and password:
                session = async_get_clientsession(self.hass)
                client = SoundsClient(session=session, logger=_LOGGER)
                
                try:
                    await client.auth.authenticate(username=username, password=password)
                except exceptions.LoginFailedError:
                    errors["base"] = "invalid_auth"
                except (exceptions.NetworkError, exceptions.APIResponseError):
                    errors["base"] = "cannot_connect"
                except Exception:
                    _LOGGER.exception("Unexpected exception during authentication")
                    errors["base"] = "unknown"
                else:
                    return self.async_create_entry(
                        title=f"BBC Sounds ({username})",
                        data={
                            CONF_USERNAME: username,
                            CONF_PASSWORD: password,
                        },
                    )
            else:
                # Anonymous access
                return self.async_create_entry(
                    title="BBC Sounds",
                    data={},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
