# CC-Packer

A simple, standalone tool to merge Fallout 4 Creation Club content into unified archives, reducing plugin count and improving load times.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-3.2.1-blue.svg)](https://github.com/jturnley/CC-Packer/releases/tag/v3.2.1)

## ✨ Features

- **Fully Standalone**: No external tools required - bsarch.exe is bundled
- **Automatic Detection**: Finds your Fallout 4 installation via Windows Registry
- **Smart Merging**: Merges all `cc*.ba2` files in your Data folder
- **Crash Prevention**: Automatically splits large texture archives (>3GB) to prevent the "Brown Face" bug
- **FO4 Localization Support**: Generated ESL files include full Fallout 4 localization metadata
- **Light Master Plugins**: ESL files use proper light master headers for optimal compatibility
- **Safety First**: Backs up all original files to `Data/CC_Backup` before making changes
- **Easy Restore**: One-click restoration to original state
- **Simple GUI**: Clean, intuitive interface - no configuration needed

## 💡 Why Use CC-Packer?

### The Problem

- Fallout 4 has a 255 plugin limit (ESM/ESP files)
- Each Creation Club item = 1 plugin slot
- With 170+ CC items now available, you could lose over half your plugin slots!
- Game performance degrades with hundreds of small BA2 archives (346+ files)

### The Solution

- Merges all CC archives into just 3-4 unified files
- Reduces plugin count from 170+ to just 2-3 light master plugins
- Improves game loading times significantly
- Frees up plugin slots for your favorite mods
- Prevents "Brown Face" bug through automatic texture splitting
- **NEW**: Full localization support for enhanced compatibility
- **STRINGS Generation**: Automatic extraction and merging of localized text

## 🆕 What's New in v3.2.1

### Detection & Performance

- **Strict CCList.txt Detection**: The `cc*` glob fallback is gone — CC content is now matched strictly against the bundled `CCList.txt`, so only official Creation Club items are ever touched (v3.2.0).
- **Bundled CCList.txt**: The authoritative list is now packaged inside the executable, so compiled builds detect CC content exactly like the source (v3.2.0).
- **Faster Extraction Verification**: Post-extraction checks short-circuit instead of re-walking a growing directory after every archive, speeding up large CC libraries (v3.2.1).

## Previous Release: v3.1.0

### Accurate CC Detection via CCList.txt

- **Official CC Database**: CC detection now uses the included `CCList.txt` file to identify only official Creation Club items
- **Reduced False Positives**: Eliminates incorrect detection of non-CC mods that match CC naming patterns
- **Improved Reliability**: 100% accuracy in identifying real Creation Club content

### Background Processing Improvements

- **Silent Merging**: Packing routine now runs completely in the background without popup windows
- **Cleaner Interface**: All progress is shown in the main GUI window
- **Code Optimizations**: Performance improvements and enhanced code documentation

### Automatic Append-Like Functionality

- **Mixed Content Detection**: Automatically detects when packed and unpacked CC content coexist
- **One-Click Update**: Clicking Merge with mixed content automatically restores from backup and repacks all items together
- **Seamless Workflow**: Add new CC content and click Merge again - no manual steps needed

## Previous Release: v3.0.0

### Content Integrity & Validation

- **Orphaned Content Detection**: Validates Creation Club content before merging by checking that each CC plugin has both required BA2 archives
- **Automatic Cleanup**: Offers to automatically delete incomplete/orphaned CC downloads before merging
- **Detailed Warnings**: Clear explanations when CC content is missing files

### Improved Detection

- **Plugin-First Scanning**: More accurate detection of creation club items
- **Mixed Content Handling**: Option to automatically restore and repack when adding new CC content after a previous merge

### Developer-Friendly

- **Comprehensive Documentation**: Full API documentation throughout codebase for easier contributions and modifications

## Previous Version Highlights (v2.0)

### Fully Standalone Operation

- **No More Archive2**: CC-Packer bundles bsarch.exe - no Creation Kit required!
- **Registry Detection**: Automatically finds Fallout 4 via Windows Registry
- **Simplified UI**: Removed Archive2 path field
- **New Output Names**: Merged archives named `CCPacked*` instead of `CCMerged*`

### Previous Features (v1.x)

- **Loose STRINGS Extraction**: STRINGS files extracted to `Data/Strings` as loose files
- **Separate Audio Archive**: Sound files packed uncompressed to prevent audio corruption
- **Vanilla-Style Naming**: Texture archives use numbered naming like vanilla
- **Merged File Detection**: Prevents accidental re-merging
- **Individual ESL per Texture Archive**: Each split texture archive gets its own ESL

## 📋 Requirements

- Windows 10/11 (64-bit)
- Fallout 4 with Creation Club content

## 📥 Installation

### Option 1: Download Binary (Recommended)

1. Download `CC-Packer_v3.1.0.zip` from [Releases](https://github.com/jturnley/CC-Packer/releases)
2. Extract anywhere on your PC
3. Run `CCPacker.exe` - no installation needed!

### Option 2: Run from Source

```bash
git clone https://github.com/jturnley/CC-Packer.git
cd CC-Packer
pip install -r requirements.txt
python main.py
```

## 🚀 Quick Start

1. **Launch**: Double-click `CCPacker.exe` (or run `python main.py`)
2. **Auto-Detection**: Tool finds Fallout 4 automatically via Windows Registry
3. **Merge**: Click "Merge CC Archives" button
4. **Wait**: Progress bar shows status (may take 5-15 minutes)
5. **Done**: Launch Fallout 4 and enjoy!

### Manual Path Selection

If auto-detection fails:
- Click "Browse..." to select your Fallout 4 folder

## 🛡️ Safety & Backup

- All original CC files are automatically backed up to `Data/CC_Backup/`
- Backup is timestamped for easy identification
- Click "Restore Original CC Archives" to undo the merge anytime
- Safe to run multiple times

## 📊 What Gets Merged

| Source Files | Output Archive | Notes |
| ------------- | ---------------- | ------- |
| `cc* - Main.ba2` | `CCPacked_Main - Main.ba2` | Compressed, meshes/scripts/etc |
| `cc* - Textures.ba2` | `CCPacked_Textures1 - Textures.ba2`, etc. | Auto-split at 7GB, each with own ESL |
| Sound files (.xwm, .wav, .fuz, .lip) | `CCPacked_Sounds - Main.ba2` | Uncompressed to prevent audio issues |
| STRINGS files | `Data/Strings/*.STRINGS` | Extracted as loose files |

**Output ESL Plugins:**

- `CCPacked_Main.esl` - Light master for main archive
- `CCPacked_Textures1.esl`, `CCPacked_Textures2.esl`, etc. - One per texture archive
- `CCPacked_Sounds.esl` - Light master for audio archive

## 🔨 Building from Source

```bash
# Install dependencies
pip install -r requirements.txt

# Build executable
build_exe.bat

# Or build release packages
build_release.bat
```

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Bethesda for Fallout 4 and the Creation Kit
- The Fallout 4 modding community for testing and feedback
- **[zilav, ElminsterAU, Sheson](https://github.com/TES5Edit/TES5Edit)** - Authors of [BSArch](https://www.nexusmods.com/newvegas/mods/64745), the archive tool bundled with CC-Packer (v2.0+). BSArch is part of the [xEdit](https://github.com/TES5Edit/TES5Edit) project and is licensed under MPL 2.0.
- **[MGuffin](https://github.com/MGuffin)** - Author of [xTranslator](https://github.com/MGuffin/xTranslator), whose open-source work on Bethesda plugin translation tools helped us understand the STRINGS file format specification used for localization support in CC-Packer (v1.0.3+). xTranslator is an invaluable tool for the modding community.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/jturnley/CC-Packer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jturnley/CC-Packer/discussions)
- **Release Notes**: [View v3.1.0 Release Notes](RELEASE_NOTES_v3.1.0.md)

## 📋 Version History

- **v3.1.0** (February 12, 2026) - CC detection via CCList.txt, background processing improvements, automatic restore & repack for mixed content
- **v3.0.0** (February 10, 2026) - Content integrity validation, orphaned CC detection, automatic cleanup, plugin-first detection
- **v2.0** (January 30, 2026) - Standalone operation with bundled BSArch, no more Archive2/Creation Kit requirement
- **v1.0.6** (November 29, 2025) - Fixed texture archives not loading (each texture archive now gets its own ESL)
- **v1.0.5** (November 29, 2025) - Disabled post-merge archive validation
- **v1.0.4** (November 28, 2025) - Enhanced BA2 validation error messages
- **v1.0.3** (November 28, 2025) - Loose STRINGS extraction, separate audio archive, BA2 verification, vanilla naming, comprehensive error handling
- **v1.0.2** (November 26, 2025) - FO4 localization support, enhanced ESL headers
- **v1.0.1** (November 26, 2025) - Smart texture archive splitting, enhanced backup system
- **v1.0.0** (November 25, 2025) - Initial release, basic CC content merging

## 🔗 Related Projects

**[BA2 Manager](https://github.com/jturnley/BA2Manager)** - Full-featured BA2 archive manager for advanced users and modders:
- Conflict detection and resolution
- Batch operations
- MO2 integration
- Custom merging rules

