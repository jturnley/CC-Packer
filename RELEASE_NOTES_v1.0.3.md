# CC-Packer v1.0.3 Release Notes

**Release Date:** November 28, 2025

## Overview

Version 1.0.3 is a significant update focused on fixing critical issues with texture corruption, audio playback, and string lookup failures that affected merged Creation Club content.

## New Features

### Separate Audio Archive
- Audio files (.xwm, .wav, .fuz, .lip) are now extracted to a dedicated uncompressed archive
- Creates `CCMerged_Sounds - Main.ba2` with `-compression=None`
- Prevents audio static and playback issues

### Loose Strings Extraction
- STRINGS files are now extracted to `Data/Strings` as loose files
- Ensures reliable lookup by the game engine regardless of archive structure
- Supports all 10 languages (en, de, es, fr, it, ja, pl, pt, ru, zh)

### Administrator Elevation Check
- Automatically detects if Fallout 4 is in a protected location (Program Files)
- Warns users to run as Administrator when needed
- Prevents cryptic permission errors during merge

### Automatic Backup Cleanup
- Old backups are automatically removed during restore
- Only the most recent backup is retained
- Saves disk space for users with limited storage

## Bug Fixes

### Texture Corruption (Critical)
- **Fixed:** Static/noise appearing on textures (e.g., BFG9000)
- **Cause:** Texture archives were using incorrect compression settings
- **Solution:** Changed to `Default` compression for texture archives

### Lookup Failed Errors (Critical)
- **Fixed:** "LOOKUP FAILED!" text appearing on world-placed items
- **Cause:** String files inside BA2 archives weren't being found by original plugins
- **Solution:** Moved string files to `Data/Strings` as loose files

### Audio Issues
- **Fixed:** Sound files potentially corrupted when compressed
- **Cause:** Audio was being packed into compressed archive
- **Solution:** Separated audio into dedicated uncompressed archive

### LIP File Support
- **Added:** `.lip` files (lip-sync data) now included in audio archive
- Ensures proper lip-sync for CC content dialogue

### ESL Plugin Flags
- **Fixed:** ESL files now use correct Light Master flags (0x201)
- Combines Master (0x01) and Light Master (0x200) flags properly

## Technical Changes

### Archive Structure
The merge now produces the following archives:

| Archive | Compression | Contents |
|---------|-------------|----------|
| `CCMerged - Main.ba2` | Default | Meshes, scripts, materials, etc. |
| `CCMerged_Sounds - Main.ba2` | None | Audio files (.xwm, .wav, .fuz, .lip) |
| `CCMerged - Textures.ba2` | Default | Texture files (.dds) |

### Plugin Structure
- `CCMerged.esl` - Loads main archive
- `CCMerged_Sounds.esl` - Loads sound archive
- Additional ESLs for texture parts if content exceeds 7GB

### String Handling
- Strings are extracted to `Data/Strings` folder
- A manifest (`moved_strings.txt`) tracks extracted files
- Restore process cleans up loose string files

## Requirements

- Windows 10/11
- Fallout 4 with Creation Club content
- Archive2.exe (from Creation Kit or Fallout 4)

## Installation

1. Download `CC-Packer_v1.0.3_Windows.zip`
2. Extract to any folder
3. Run `CCPacker.exe`
4. If FO4 is in Program Files, run as Administrator

## Upgrade Notes

If upgrading from v1.0.2 or earlier:
1. Use "Restore Backup" to restore original CC files
2. Run the merge again with v1.0.3
3. The new archive structure will be created automatically

## Changelog Summary

### v1.0.3 (November 28, 2025)
- Separate audio archive (uncompressed)
- Loose strings extraction
- Administrator elevation check
- Automatic backup cleanup
- Fixed texture corruption
- Fixed lookup failed errors
- Fixed audio issues
- Added LIP file support

### v1.0.2 (November 26, 2025)
- Full FO4 localization support in ESL files
- Enhanced plugin metadata structure

### v1.0.1 (November 26, 2025)
- Fixed sound playback issues
- Separate uncompressed sound archive

### v1.0.0 (November 26, 2025)
- Initial release
- Core merging functionality
- PyQt6 GUI
