"""Media source for BBC Sounds."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.media_player import MediaClass, MediaType
from homeassistant.components.media_source import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
    Unresolvable,
)
from homeassistant.core import HomeAssistant

from sounds import SoundsClient

from .const import DOMAIN

if TYPE_CHECKING:
    from . import BBCSoundsConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_get_media_source(hass: HomeAssistant) -> BBCSoundsMediaSource:
    """Set up BBC Sounds media source."""
    return BBCSoundsMediaSource(hass)


class BBCSoundsMediaSource(MediaSource):
    """Provide BBC Sounds stations as a media source."""

    name = "BBC Sounds"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the media source."""
        super().__init__(DOMAIN)
        self.hass = hass

    def _get_client(self) -> SoundsClient | None:
        """Get the SoundsClient from the config entry."""
        entries = self.hass.config_entries.async_entries(DOMAIN)
        if entries:
            entry: BBCSoundsConfigEntry = entries[0]
            return entry.runtime_data
        return None

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve a media item to a playable URL."""
        client = self._get_client()
        if not client:
            raise Unresolvable("BBC Sounds not configured")

        identifier = item.identifier
        if not identifier:
            raise Unresolvable("No station specified")

        # Identifier format: "live/{station_id}" e.g. "live/bbc_radio_fourfm"
        parts = identifier.split("/", 1)
        if len(parts) != 2:
            raise Unresolvable(f"Invalid identifier format: {identifier}")

        media_type, station_id = parts

        try:
            if media_type == "live":
                # Log auth state for debugging
                _LOGGER.debug(
                    "Resolving stream for %s - client.auth.is_logged_in: %s",
                    station_id,
                    client.auth.is_logged_in
                )
                
                # Get station with stream URL using stations service
                # This properly handles JWT token authentication
                station = await client.stations.get_station(
                    station_id, include_stream=True, stream_format="hls"
                )
                
                if not station:
                    raise Unresolvable(f"Station not found: {station_id}")
                
                # station.stream is a string URL
                if not station.stream:
                    raise Unresolvable(f"Could not get stream for {station_id}")
                
                _LOGGER.debug("Resolved %s to stream: %s", station_id, station.stream)
                
                return PlayMedia(
                    url=station.stream,
                    mime_type="application/vnd.apple.mpegurl",
                )
            else:
                # For on-demand content, use get_by_pid
                episode = await client.streaming.get_by_pid(
                    station_id, include_stream=True, stream_format="hls"
                )
                # episode.stream is a string URL for on-demand content
                if not episode or not episode.stream:
                    raise Unresolvable(f"Could not get stream for {station_id}")
                return PlayMedia(
                    url=episode.stream,
                    mime_type="application/vnd.apple.mpegurl",
                )
        except Exception as err:
            error_msg = str(err)
            _LOGGER.error("Error resolving media for %s: %s", identifier, error_msg)
            
            # Provide helpful error messages for common issues
            if "no token could be provided" in error_msg.lower():
                raise Unresolvable(
                    "BBC Sounds streaming requires a UK IP address. "
                    "The BBC geo-restricts live radio streams to UK listeners only. "
                    "If you're in the UK and seeing this error, try adding BBC account "
                    "credentials in the integration settings."
                ) from err
            elif "401" in error_msg or "unauthorised" in error_msg.lower():
                raise Unresolvable(
                    "Authentication failed. Please check your BBC account credentials "
                    "in the integration settings."
                ) from err
            
            raise Unresolvable(f"Could not resolve stream: {err}") from err

    async def async_browse_media(
        self, item: MediaSourceItem
    ) -> BrowseMediaSource:
        """Browse available BBC radio stations."""
        client = self._get_client()
        
        if not client:
            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=None,
                media_class=MediaClass.CHANNEL,
                media_content_type=MediaType.MUSIC,
                title="BBC Sounds",
                can_play=False,
                can_expand=False,
                children=[],
            )

        identifier = item.identifier if item.identifier else ""

        # Root or "live" - show live stations
        if identifier == "" or identifier == "live":
            return await self._browse_live_stations(client)

        # Unknown path
        return await self._browse_root()

    async def _browse_root(self) -> BrowseMediaSource:
        """Browse root folder."""
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier="",
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.MUSIC,
            title="BBC Sounds",
            can_play=False,
            can_expand=True,
            children=[
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier="live",
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.MUSIC,
                    title="Live Radio",
                    can_play=False,
                    can_expand=True,
                )
            ],
        )

    async def _browse_live_stations(self, client: SoundsClient) -> BrowseMediaSource:
        """Browse live radio stations dynamically from API."""
        children = []

        try:
            stations = await client.stations.get_stations()
            
            for station in stations:
                if not station or not station.item_id:
                    continue

                # Get station name
                name = "Unknown Station"
                if station.network and station.network.short_title:
                    name = station.network.short_title
                elif hasattr(station, "titles") and station.titles:
                    name = station.titles.get("primary", "Unknown Station")

                # Get station logo
                thumbnail = None
                if station.network and station.network.logo_url:
                    thumbnail = station.network.logo_url
                elif hasattr(station, "image_url") and station.image_url:
                    thumbnail = station.image_url

                children.append(
                    BrowseMediaSource(
                        domain=DOMAIN,
                        identifier=f"live/{station.item_id}",
                        media_class=MediaClass.CHANNEL,
                        media_content_type=MediaType.MUSIC,
                        title=name,
                        can_play=True,
                        can_expand=False,
                        thumbnail=thumbnail,
                    )
                )
        except Exception as err:
            _LOGGER.error("Error fetching BBC stations: %s", err)
            # Fallback to popular stations if API fails
            children = self._get_fallback_stations()

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier="live",
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.MUSIC,
            title="Live Radio",
            can_play=False,
            can_expand=True,
            children=children,
        )

    def _get_fallback_stations(self) -> list[BrowseMediaSource]:
        """Return popular stations as fallback if API fails."""
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
        
        return [
            BrowseMediaSource(
                domain=DOMAIN,
                identifier=f"live/{pid}",
                media_class=MediaClass.CHANNEL,
                media_content_type=MediaType.MUSIC,
                title=name,
                can_play=True,
                can_expand=False,
            )
            for name, pid in stations
        ]
