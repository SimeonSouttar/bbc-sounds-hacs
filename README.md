# BBC Sounds for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/SimeonSouttar/bbc-sounds-hacs)](https://github.com/SimeonSouttar/bbc-sounds-hacs/releases)

Listen to BBC Sounds live radio content directly from Home Assistant.

## Features

- **Live Radio**: Stream BBC radio stations (Radio 1, Radio 2, Radio 4, 6 Music, World Service, etc.)
- **Dynamic Station List**: Automatically fetches available stations from BBC
- **Media Browser**: Browse and play stations via the Home Assistant Media Browser
- **Cast Support**: Cast BBC radio to any media player (Chromecast, Sonos, etc.)
- **Optional BBC Account**: Login for access to UK-only content

## Installation via HACS

1. Open HACS in Home Assistant
2. Go to **Integrations** → Menu (⋮) → **Custom repositories**
3. Enter: `https://github.com/SimeonSouttar/bbc-sounds-hacs`
4. Select **Integration** as the category
5. Click **Add**, then find and download **BBC Sounds**
6. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **BBC Sounds**
4. (Optional) Enter your BBC account credentials for UK-only content

## Usage

### Media Browser

Open the Media Browser panel in Home Assistant and select **BBC Sounds** → **Live Radio** to see available stations.

### Automations

```yaml
service: media_player.play_media
target:
  entity_id: media_player.living_room_speaker
data:
  media_content_type: music
  media_content_id: media-source://bbc_sounds/live/bbc_radio_fourfm
```

**Common Station IDs:**
| Station | ID |
|---------|-----|
| BBC Radio 1 | `bbc_radio_one` |
| BBC Radio 2 | `bbc_radio_two` |
| BBC Radio 3 | `bbc_radio_three` |
| BBC Radio 4 | `bbc_radio_fourfm` |
| BBC Radio 4 Extra | `bbc_radio_four_extra` |
| BBC Radio 5 Live | `bbc_radio_five_live` |
| BBC Radio 6 Music | `bbc_6music` |
| BBC World Service | `bbc_world_service` |

## Disclaimer

This is a custom integration and is not officially affiliated with the BBC.

## Credits

- [auntie-sounds](https://github.com/kieranhogg/auntie-sounds) library by @kieranhogg
- [Music Assistant](https://github.com/music-assistant/server) for inspiration
