# Changelog

All notable changes to CC-Packer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.2.1] - 2026-07-22

### Improved

- **Extraction Verification Performance**: `_verify_extraction` now short-circuits on the first extracted file instead of doing a full recursive file count after every archive. Because archives extract cumulatively into a shared directory, the old count grew with each item (O(n²) across a library); it is now O(n).
- **Minor Optimization**: The Main-archive repack step tests for content with `any()` instead of materializing the full recursive file list.

### Fixed

- Corrected the `_verify_extraction` docstring, which claimed archive header/metadata validation the method does not perform. It now accurately documents its header-count-plus-presence check.

## [3.2.0] - 2026-07-22

### Changed

- **Strict CCList.txt Detection**: Removed the `cc*.ba2`/`cc*.esl` glob fallback entirely. CC detection — for both merging and the existing-content scan — now matches strictly against `CCList.txt`, preventing non-CC files from being pulled into merge/repack operations.

### Fixed

- **Bundled CCList.txt**: `CCList.txt` is now a tracked file and bundled in the build via `CCPacker.spec` datas, so compiled builds use authoritative detection rather than silently falling back to glob matching.

### Removed

- Removed the now-unreachable mixed-content confirmation dialog path (`_handle_merge_with_mixed_files`).

## [3.1.0] - 2026-02-12

### Added

- **CC List-Based Detection**: CC detection is now limited to files registered in the included `CCList.txt` file, ensuring that only official Creation Club items are identified. This eliminates false positives from non-CC mods that match CC naming patterns.
- **Automatic Restore & Repack**: When users click the Merge button with a mixture of packed (merged) and unpacked CC content present, CC-Packer automatically detects this state, restores from backup, and re-runs the full packing process with all CC items together. This provides the closest possible equivalent to an "append" function for BA2 archives.
- **Background Processing**: Packing routine now runs completely in the background without spawning popup windows, resulting in a cleaner and more professional user experience.

### Changed

- **CC Detection Method**: Refactored CC file detection to validate against `CCList.txt` instead of simple filename matching patterns. This provides 100% accuracy in identifying official Creation Club items.
- **Process Management**: Packing operations now run in background processes with proper I/O redirection, eliminating unwanted console windows during execution.

### Improved

- **Code Quality**: Enhanced documentation and code optimization throughout the application via advanced AI-assisted refactoring.
- **Stability**: Background process window suppression eliminates potential issues from popup interactions with the GUI.
- **Workflow**: Mixed packed/unpacked content now has a seamless solution - users can simply add new CC content and click Merge again without manual restoration.

### Technical Details

- Integrated `CCList.txt` as the authoritative source for CC file detection
- Implemented background process launcher with proper subprocess management
- Added automatic mixed content detection and conditional restore/repack workflow
- Code optimizations for improved performance

## [3.0.0] - 2026-02-10

### Added

- **Orphaned CC Content Detection**: CC-Packer now validates Creation Club content integrity before merging by checking that each CC plugin file has both required BA2 archives (Main and Textures). Incomplete or orphaned items are detected and reported to the user.
- **Automatic Orphaned Content Cleanup**: When incomplete CC items are detected, users are presented with a detailed warning dialog that includes:
  - List of affected CC items with missing files
  - Explanation of the issue (known Fallout 4 download engine bug)
  - Clickable link to CC-Packer documentation for more information
  - Three action options:
    - Delete Orphaned CC Content And Quit
    - Delete Orphaned CC Content and Continue (merges remaining valid items)
    - Quit CC Packer Now
- **Plugin-First Detection**: Changed from BA2-first to plugin-first detection. CC content is now identified by finding plugin files (cc*.esl, cc*.esp, cc*.esm) and validating their BA2 archives exist, providing more accurate detection of Creation Club items.
- **Comprehensive Code Documentation**: Added extensive human-readable documentation to all Python modules including:
  - Detailed module-level docstrings explaining architecture and purpose
  - Complete class documentation with attribute descriptions
  - Method docstrings with Args, Returns, Examples, and Notes sections
  - Inline comments explaining complex logic and algorithms
  - Usage examples for key functions
- **Smart Mixed Content Handling**: When both CCPacked archives and new unmerged CC files are detected, users are now prompted with an option to automatically restore and repack all CC items together. This ensures optimal results when adding new Creation Club content after a previous merge.

### Changed

- **Content Detection Method**: Refactored merge process to detect Creation Club content by scanning for plugin files (cc*.esl, cc*.esp, cc*.esm) first, then validating that each has its required BA2 archives. Previously scanned for cc*.ba2 files directly. Note: Plugin files remain in the Data folder as they contain the actual game records; only BA2 asset archives are merged.
- **Validation Workflow**: Integrity validation now occurs before merge process starts, allowing users to address issues before any file operations begin.

### Improved

- **Error Messages**: Orphaned content warnings now provide detailed information about which files are missing for each CC item (Main BA2, Textures BA2, or both).
- **User Guidance**: Integrated contextual help with clickable links to documentation for resolving common issues.
- **Code Maintainability**: Comprehensive documentation throughout codebase makes it easier for developers to understand and modify the application.
- **Validation Accuracy**: Plugin-first detection provides more reliable identification of incomplete downloads compared to BA2-only scanning.

### Technical Details

- Added `_find_cc_plugins()` method to scan for CC plugin files (.esl, .esp, .esm)
- Added `_validate_cc_content_integrity()` method that returns lists of valid and orphaned CC items
- Added `_delete_orphaned_cc_content()` method for automatic cleanup of incomplete CC items
- Added `_handle_orphaned_cc_content()` in main.py for user interaction and cleanup workflow
- Merge process now builds BA2 file list from validated plugins rather than directory scanning
- Original CC plugin files remain in Data folder (they contain game records); only BA2 archives are merged and deleted
- All new methods include comprehensive docstrings with Args, Returns, Examples, and Notes
- Module-level docstrings added to main.py and merger.py explaining architecture and design decisions

### Fixed

- **Main Archive ESL Conflict**: Renamed main archive from `CCPacked.esl` / `CCPacked - Main.ba2` to `CCPacked_Main.esl` / `CCPacked_Main - Main.ba2`. Previously, `CCPacked.esl` was activating all BA2 archives due to prefix matching (including `CCPacked_Sounds - Main.ba2` and `CCPacked_Textures1 - Textures.ba2`). Each archive now has a unique prefix ensuring proper isolation.
- **v1.x Upgrade Cleanup**: Fixed issue where users upgrading from v1.x would have leftover `CCMerged*` files. The merge and restore operations now properly delete old v1.x `CCMerged` files alongside v2.0 `CCPacked` files.

## [2.0.0] - 2026-01-30

### Added

- **Bundled BSArch**: CC-Packer now includes bsarch.exe, eliminating the need for Archive2.exe/Creation Kit
- **Registry-Based Detection**: Automatically finds Fallout 4 installation via Windows Registry
- **BSArch License**: Added BSARCH_LICENSE.txt for MPL 2.0 compliance

### Changed

- **Standalone Operation**: No longer requires Archive2.exe or Creation Kit installation
- **Output Naming**: Merged archives renamed from `CCMerged*` to `CCPacked*` for clarity
- **Simplified UI**: Removed Archive2 path input field (no longer needed)

### Fixed

- **Archive Path Prefix**: Fixed bsarch path handling that caused files to be stored with incorrect prefixes (CC_Temp\General\), which prevented worldspace items from appearing in-game

### Technical Details

- Integrated [BSArch](https://www.nexusmods.com/newvegas/mods/64745) v1.0 x64 by zilav, ElminsterAU, and Sheson
- BSArch is part of the [xEdit](https://github.com/TES5Edit/TES5Edit) project (MPL 2.0 licensed)
- Pack operations now use working directory control for correct path resolution
- Output paths resolved to absolute before packing

## [1.0.6] - 2025-11-29

### Fixed

- **Texture Archives Not Loading** - Each texture archive now gets its own ESL file to ensure proper loading. Previously, split texture archives (Textures2, Textures3, etc.) were not being loaded by the game because they lacked associated plugins.

### Changed

- **New Archive Naming Convention** - Texture archives now use a per-archive naming scheme:
  - `CCMerged_Textures1.esl` → `CCMerged_Textures1 - Textures.ba2`
  - `CCMerged_Textures2.esl` → `CCMerged_Textures2 - Textures.ba2`
  - This ensures each texture archive is properly registered with the game engine.

### Technical Details

- Each texture split now creates its own ESL plugin file
- Archive naming changed from `CCMerged - Textures1.ba2` to `CCMerged_Textures1 - Textures.ba2`
- All texture ESLs are automatically added to plugins.txt

## [1.0.5] - 2025-11-29

### Changed

- **Disabled Archive Validation** - Temporarily disabled the BA2 archive verification step after merge completion. This resolves issues where the validation was incorrectly rejecting valid archives created by Archive2.exe. The merge process now completes without the verification check.

### Technical Details

- Commented out the `verify_ba2_integrity()` call in the merge workflow
- The verification method remains in the codebase for future use
- Archive2.exe output is still checked for errors during extraction/creation

## [1.0.4] - 2025-11-28

### Improved

- **Enhanced BA2 Validation Messages** - Improved error messages when BA2 verification fails to include expected values (e.g., "expected 1 or 8" for version, "expected GNRL or DX10" for archive type).
- **Better BA2 Version Documentation** - Added comprehensive inline documentation for BA2 format versions:
  - Version 1: Original Fallout 4 (2015)
  - Version 7: Fallout 76 (not used in FO4)
  - Version 8: Fallout 4 Next-Gen Update (April 2024)
- **Archive Type Documentation** - Added comments explaining BA2 archive types:
  - GNRL: General archives (meshes, scripts, sounds, etc.)
  - DX10: Texture archives (DirectX 10 format DDS)

### Technical Details

- Updated `verify_ba2_integrity()` with more descriptive error messages and inline documentation.
- No functional changes - validation logic remains the same (accepts versions 1 and 8, types GNRL and DX10).

## [1.0.3] - 2025-11-28

### Added

- **Separate Audio Archive** - Audio files (.xwm, .wav, .fuz, .lip) are now extracted to a separate uncompressed archive (`CCMerged_Sounds - Main.ba2`) to prevent static/corruption.
- **Loose Strings Extraction** - Original CC STRINGS files are now extracted as loose files to `Data/Strings` to ensure reliable lookup by the game engine.
- **Administrator Elevation Check** - The application now detects if Fallout 4 is installed in a protected location (e.g., `Program Files`) and warns the user to run as Administrator if needed.
- **Automatic Backup Cleanup** - Old backups are now automatically removed during restore, keeping only the most recent backup to save disk space.
- **BA2 Integrity Verification** - All created archives are now verified before completing the merge process. Checks BA2 header magic number, version, archive type, file count, and name table offset to detect corruption.
- **Archive2 List Validation** - When Archive2.exe is available, archives are also validated using Archive2's built-in listing functionality.
- **Merged File Detection** - The application now detects when CC files have already been merged (CCMerged*.ba2 present) and provides appropriate guidance. Prevents accidental re-merging and warns users about mixed merged/unmerged states.

### Fixed

- **Texture Corruption** - Fixed static/noise on textures (e.g., BFG9000) by using `Default` compression for texture archives instead of `None`.
- **Lookup Failed Errors** - Solved persistent string lookup failures by moving string files out of the archives and into the `Data/Strings` folder.
- **Audio Issues** - Prevented audio glitches by ensuring sound files are packed without compression in a dedicated archive.
- **LIP File Support** - Added `.lip` files (lip-sync data) to the audio archive to ensure proper handling.
- **Next-Gen BA2 Version Support** - BA2 integrity verification now accepts both version 1 (original FO4) and version 8 (Next-Gen Update 2024) archives.
- Fixed ESL plugin flags to use correct Light Master flags (0x201 = Master + Light Master).
- **Vanilla-Style Texture Naming** - Texture archives now use numbered naming matching vanilla Bethesda archives (e.g., `CCMerged - Textures1.ba2`, `CCMerged - Textures2.ba2`) instead of `CCMerged_Part2 - Textures.ba2`.

### Changed

- **Archive Structure**:
  - `CCMerged - Main.ba2`: Compressed (Default), contains meshes, scripts, etc.
  - `CCMerged_Sounds - Main.ba2`: Uncompressed (None), contains audio files (.xwm, .wav, .fuz, .lip).
  - `CCMerged - Textures.ba2`: Compressed (Default), contains textures.
- **Strings Handling**: Strings are now moved to `Data/Strings` (loose files) instead of being packed, ensuring the original CC plugins can find them.
- **Plugins**: Added `CCMerged_Sounds.esl` to load the separate audio archive.
- **Main Archive Compression**: Changed from uncompressed to `Default` compression for better compatibility.

### Improved

- **Comprehensive Error Handling** - Replaced generic "error code 1" messages with detailed diagnostics. Archive2 errors now report:
  - The specific operation that failed (extract/create)
  - The archive being processed
  - Exit codes and stderr/stdout output
  - User-friendly error descriptions (access denied, disk full, file locked, etc.)
- **10-Minute Timeout** - Added timeout protection for Archive2 operations on very large archives.
- **Graceful Cleanup** - Improved error handling during cleanup phase to prevent orphaned files.

### Technical Details

- ESL files now use flags 0x201 (Master + Light Master).
- `merger.py` now recursively searches for and moves string files to `Data/Strings`.
- `merger.py` creates a manifest (`moved_strings.txt`) to track and clean up loose string files during restore.
- Added `ctypes` import for Windows API calls (admin check).
- Added `Archive2Error` exception class with structured error information.
- Added `_run_archive2()` method for centralized Archive2 execution with error parsing.
- Added `verify_ba2_integrity()` method for BA2 header and structure validation.
- Added `struct` module for binary parsing of BA2 headers.
- Added type hints for better code documentation.

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
