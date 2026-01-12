"""Media source for BBC Sounds."""
from __future__ import annotations

import logging


from homeassistant.components.media_source.error import MediaSourceError, Unresolvable
from homeassistant.components.media_source.models import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
)
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_USERNAME

from .const import DOMAIN
from .sounds import SoundsClient

_LOGGER = logging.getLogger(__name__)

async def async_get_media_source(hass: HomeAssistant) -> MediaSource:
    """Set up BBC Sounds media source."""
    return BBCSoundsMediaSource(hass)


class BBCSoundsMediaSource(MediaSource):
    """Provide BBC Sounds as media source."""

    name = "BBC Sounds"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize BBC Sounds media source."""
        super().__init__(DOMAIN)
        self.hass = hass

    @property
    def client(self) -> SoundsClient | None:
        """Return the SoundsClient."""
        # We assume single instance for now as per manifest
        if not self.hass.data.get(DOMAIN):
            return None
        # Return the first available client
        return next(iter(self.hass.data[DOMAIN].values()), None)

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve media to a url."""
        client = self.client
        if not client:
            raise Unresolvable("BBC Sounds not configured")

        identifier = item.identifier
        # Identifier format: "type/id" e.g. "live/bbc_radio_fourfm"
        
        parts = identifier.split("/", 1)
        if len(parts) != 2:
             raise Unresolvable(f"Invalid identifier: {identifier}")
        
        media_type, item_id = parts

        try:
            # For live radio, we need to use get_live_stream
            if media_type == "live":
                stream_url = await client.streaming.get_live_stream(
                    item_id, stream_format="hls"
                )
                return PlayMedia(stream_url, "application/vnd.apple.mpegurl")
            
            # For other types (future), use get_by_pid
            stream = await client.streaming.get_by_pid(item_id, stream_format="hls")
            
            if not stream or not stream.url:
                 raise Unresolvable(f"Could not resolve stream for {item_id}")

            # Determine mime type
            mime_type = "application/vnd.apple.mpegurl"
            if stream.url.endswith(".mp3"):
                mime_type = "audio/mpeg"
            elif stream.url.endswith(".mpd"):
                mime_type = "application/dash+xml"

            return PlayMedia(stream.url, mime_type)
            
        except Exception as err:
            raise Unresolvable(f"Could not resolve media: {err}") from err


    async def async_browse_media(
        self,
        media_content_id: MediaSourceItem | str | None = None,
    ) -> BrowseMediaSource:
        """Browse media."""
        try:
            # Handle MediaSourceItem being passed as first argument
            if isinstance(media_content_id, MediaSourceItem):
                media_content_id = media_content_id.identifier

            client = self.client
            if not client:
                raise MediaSourceError("BBC Sounds not configured")

            if media_content_id is None or media_content_id == "":
                return await self._async_browse_root()
            
            parts = media_content_id.split("/", 1)
            category = parts[0]
            
            if category == "live":
                return await self._async_browse_live()
            
            # Future: Add "my_sounds" etc.
            
            raise MediaSourceError(f"Unknown category {category}")
        except Exception as err:
            raise

    async def _async_browse_root(self) -> BrowseMediaSource:
        """Browse root folder."""
        children = [
            BrowseMediaSource(
                domain=DOMAIN,
                identifier="live",
                media_class="directory",
                media_content_type="library",
                title="Live Radio",
                can_play=False,
                can_expand=True,
            )
        ]
        
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier="",
            media_class="directory",
            media_content_type="library",
            title="BBC Sounds",
            can_play=False,
            can_expand=True,
            children_media_class="directory",
            children=children,
            thumbnail="/api/bbc_sounds/logo",
        )

    async def _async_browse_live(self) -> BrowseMediaSource:
        """Browse live stations."""
        # Hardcoding popular stations first or fetching from API?
        # Let's try to fetch from API if possible, otherwise hardcode some popular ones as fallback or initial implementation.
        # But SoundsClient doesn't seem to have a simple "get_all_stations" method exposed at top level?
        # Reference implementation does `client.stations.get_stations()`? 
        # I need to check `stations` module of `auntie-sounds` or how reference implementation gets list.
        # Reference `__init__.py` has `_convert_track` etc, but browsing lists?
        # Reference uses `get_network_stations` or `get_stations`?
        
        # Checking `Stations` in `auntie-sounds` requires reading `sounds/stations.py` usually.
        # But let's assume `client.stations` exists.
        # The reference implementation `_fetch_menu` calls `client.personal.get_experience_menu` for authenticated users.
        # For general browsing, `Adaptor` converts things.
        
        # Let's list specific popular stations for now to ensure Radio 4 works as requested.
        # Radio 4 FM PID: bbc_radio_fourfm
        # Radio 4 LW PID: bbc_radio_fourlw
        
        stations = [
            ("BBC Radio 1", "bbc_radio_one"),
            ("BBC Radio 2", "bbc_radio_two"),
            ("BBC Radio 3", "bbc_radio_three"),
            ("BBC Radio 4", "bbc_radio_fourfm"),
            ("BBC Radio 4 Extra", "bbc_radio_four_extra"),
            ("BBC Radio 5 Live", "bbc_radio_five_live"),
            ("BBC Radio 6 Music", "bbc_6music"),
            ("BBC World Service", "bbc_world_service"),
        ]
        
        children = []
        for name, pid in stations:
            children.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"live/{pid}",
                    media_class="music",
                    media_content_type="audio/mpeg",
                    title=name,
                    can_play=True,
                    can_expand=False,
                )
            )
            
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier="live",
            media_class="directory",
            media_content_type="library",
            title="Live Radio",
            can_play=False,
            can_expand=True,
            children_media_class="music",
            children=children,
        )
