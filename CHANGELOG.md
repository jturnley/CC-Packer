# Changelog

All notable changes to CC-Packer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.3] - 2025-11-28

### Added

- **Separate Audio Archive** - Audio files (.xwm, .wav, .fuz, .lip) are now extracted to a separate uncompressed archive (`CCMerged_Sounds - Main.ba2`) to prevent static/corruption.
- **Loose Strings Extraction** - Original CC STRINGS files are now extracted as loose files to `Data/Strings` to ensure reliable lookup by the game engine.
- **Administrator Elevation Check** - The application now detects if Fallout 4 is installed in a protected location (e.g., `Program Files`) and warns the user to run as Administrator if needed.
- **Automatic Backup Cleanup** - Old backups are now automatically removed during restore, keeping only the most recent backup to save disk space.

### Fixed

- **Texture Corruption** - Fixed static/noise on textures (e.g., BFG9000) by using `Default` compression for texture archives instead of `None`.
- **Lookup Failed Errors** - Solved persistent string lookup failures by moving string files out of the archives and into the `Data/Strings` folder.
- **Audio Issues** - Prevented audio glitches by ensuring sound files are packed without compression in a dedicated archive.
- **LIP File Support** - Added `.lip` files (lip-sync data) to the audio archive to ensure proper handling.
- Fixed ESL plugin flags to use correct Light Master flags (0x201 = Master + Light Master).

### Changed

- **Archive Structure**:
  - `CCMerged - Main.ba2`: Compressed (Default), contains meshes, scripts, etc.
  - `CCMerged_Sounds - Main.ba2`: Uncompressed (None), contains audio files (.xwm, .wav, .fuz, .lip).
  - `CCMerged - Textures.ba2`: Compressed (Default), contains textures.
- **Strings Handling**: Strings are now moved to `Data/Strings` (loose files) instead of being packed, ensuring the original CC plugins can find them.
- **Plugins**: Added `CCMerged_Sounds.esl` to load the separate audio archive.
- **Main Archive Compression**: Changed from uncompressed to `Default` compression for better compatibility.

### Technical Details

- ESL files now use flags 0x201 (Master + Light Master).
- `merger.py` now recursively searches for and moves string files to `Data/Strings`.
- `merger.py` creates a manifest (`moved_strings.txt`) to track and clean up loose string files during restore.
- Added `ctypes` import for Windows API calls (admin check).

## [1.0.2] - 2025-11-26

### Added

- Full FO4 localization support in generated ESL files
- Proper ESL metadata with HEDR, CNAM, SNAM, ONAM, INTV, and INCC subrecords
- Enhanced plugin compatibility with Vortex and MO2 plugin managers
- Comprehensive release process documentation for future releases

### Improved

- ESL file generation now includes complete metadata structure
- Better plugin recognition in Fallout 4
- Improved release workflow with documented procedures

## [1.0.1] - 2025-11-26

### Fixed

- Fixed sound playback issues by packing sound files (`.xwm`, `.wav`, `.fuz`) into a separate uncompressed archive.
- Updated `Archive2` arguments to correctly handle uncompressed packing.

## [1.0.0] - 2025-11-25

### Added

- Initial release of CC-Packer
- Automatic Fallout 4 installation detection
- Automatic Archive2.exe detection
- Smart merging of Creation Club BA2 archives
- Automatic splitting of large texture archives (>3GB)
- Safe backup system for original CC files
- One-click restore functionality
- Simple PyQt6-based GUI
- Progress bar for merge operations
- Comprehensive error handling and user feedback
- Build scripts for creating standalone executables

### Features

- Merges cc*-Main.ba2 → CCMerged-Main.ba2
- Merges cc*-Textures.ba2 → CCMerged-Textures.ba2 (auto-split if >3GB)
- Merges cc*-Geometry.ba2 → CCMerged-Geometry.ba2
- Merges cc*-Voices_en.ba2 → CCMerged-Voices_en.ba2
- Merges all other archive types appropriately
- Prevents "Brown Face" bug through smart texture splitting
- Reduces plugin count from 70+ to 1
- Improves game load times by 10-30%

[1.0.0]: https://github.com/jturnley/CC-Packer/releases/tag/v1.0.0
