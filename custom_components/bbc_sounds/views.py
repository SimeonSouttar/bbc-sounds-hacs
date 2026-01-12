"""HTTP Views for BBC Sounds."""
from __future__ import annotations

import os
from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN

class BBCSoundsLogoView(HomeAssistantView):
    """View to serve the BBC Sounds logo."""

    requires_auth = False
    url = "/api/bbc_sounds/logo"
    name = "api:bbc_sounds:logo"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Handle GET request."""
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        return web.FileResponse(logo_path)
