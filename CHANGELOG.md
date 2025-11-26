# Changelog

All notable changes to CC-Packer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
