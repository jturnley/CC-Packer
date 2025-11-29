# CC-Packer v1.0.6 Release Notes

**Release Date:** November 29, 2025

## Overview

This release fixes a critical issue where split texture archives were not being loaded by the game.

## Changes

### Fixed: Texture Archives Not Loading

Each texture archive now gets its own ESL file to ensure proper loading. Previously, split texture archives (Textures2, Textures3, etc.) were not being loaded by the game because they lacked associated plugins.

### New Archive Naming Convention

Texture archives now use a per-archive naming scheme:

| Plugin | Archive |
|--------|---------|
| `CCMerged.esl` | `CCMerged - Main.ba2` |
| `CCMerged_Sounds.esl` | `CCMerged_Sounds - Main.ba2` |
| `CCMerged_Textures1.esl` | `CCMerged_Textures1 - Textures.ba2` |
| `CCMerged_Textures2.esl` | `CCMerged_Textures2 - Textures.ba2` |

This ensures each texture archive is properly registered with the game engine.

## Upgrade Instructions

If you previously ran v1.0.5 or earlier:

1. Run CC-Packer and click **Restore Backup**
2. Run the merge again with v1.0.6
3. The new archive/ESL structure will be created

## Technical Details

- Each texture split now creates its own ESL plugin file
- Archive naming changed from `CCMerged - Textures1.ba2` to `CCMerged_Textures1 - Textures.ba2`
- All texture ESLs are automatically added to plugins.txt

## Compatibility

- Windows 10/11
- Fallout 4 (all versions including Next-Gen Update)
- Fallout 4 Creation Kit (for Archive2.exe)

## Changelog Summary

### v1.0.6 (November 29, 2025)

- Fixed texture archives not loading
- New per-archive ESL naming convention

### v1.0.5 (November 29, 2025)

- Disabled post-merge archive validation

### v1.0.4 (November 28, 2025)

- Enhanced BA2 validation error messages

### v1.0.3 (November 28, 2025)

- Separate audio archive, loose strings, BA2 verification

### v1.0.2 (November 26, 2025)

- Full FO4 localization support in ESL files

### v1.0.1 (November 26, 2025)

- Fixed sound playback issues

### v1.0.0 (November 25, 2025)

- Initial release
