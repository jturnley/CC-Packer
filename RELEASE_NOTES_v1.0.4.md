# CC-Packer v1.0.4 Release Notes

**Release Date:** November 28, 2025

## Overview

This is a minor documentation and error message improvement release. No functional changes to the merging process.

## Improvements

### Enhanced BA2 Validation Messages

- Improved error messages when BA2 verification fails to include expected values
- Now shows "expected 1 or 8" for version errors
- Now shows "expected GNRL or DX10" for archive type errors
- Makes debugging user-reported issues easier

### Better Code Documentation

- Added comprehensive inline documentation for BA2 format versions:
  - **Version 1**: Original Fallout 4 (2015)
  - **Version 7**: Fallout 76 (not used in FO4)
  - **Version 8**: Fallout 4 Next-Gen Update (April 2024)
  
- Added comments explaining BA2 archive types:
  - **GNRL**: General archives (meshes, scripts, sounds, etc.)
  - **DX10**: Texture archives (DirectX 10 format DDS)

## Technical Details

- Updated `verify_ba2_integrity()` method in `merger.py` with:
  - More descriptive error messages
  - Inline documentation for version numbers
  - Inline documentation for archive types
- No changes to validation logic - still accepts versions 1 and 8, types GNRL and DX10

## Compatibility

- Windows 10/11
- Fallout 4 (all versions including Next-Gen Update)
- Fallout 4 Creation Kit (for Archive2.exe)

## Changelog Summary

### v1.0.4 (November 28, 2025)
- Enhanced BA2 validation error messages
- Better inline code documentation

### v1.0.3 (November 28, 2025)
- Separate audio archive for sound files
- Loose strings extraction
- Administrator elevation check
- BA2 integrity verification
- Next-Gen BA2 version 8 support
- Vanilla-style texture naming

### v1.0.2 (November 26, 2025)
- Full FO4 localization support in ESL files
- Enhanced plugin compatibility

### v1.0.1 (November 26, 2025)
- Fixed sound playback issues

### v1.0.0 (November 25, 2025)
- Initial release
