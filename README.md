# CC-Packer

A simple, standalone tool to merge Fallout 4 Creation Club content into unified archives, reducing plugin count and improving load times.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.0.3-blue.svg)](https://github.com/jturnley/CC-Packer/releases/tag/v1.0.3)

## ✨ Features

- **Automatic Detection**: Finds your Fallout 4 installation and Archive2.exe
- **Smart Merging**: Merges all `cc*.ba2` files in your Data folder
- **Crash Prevention**: Automatically splits large texture archives (>3GB) to prevent the "Brown Face" bug
- **FO4 Localization Support**: Generated ESL files include full Fallout 4 localization metadata (v1.0.2+)
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

## 🆕 What's New in v1.0.3?

### Major Improvements

- **Loose STRINGS Extraction**: STRINGS files are now extracted to `Data/Strings` as loose files for reliable localization lookup
- **Separate Audio Archive**: Sound files (.xwm, .wav, .fuz, .lip) are packed uncompressed in a dedicated archive to prevent audio corruption
- **BA2 Integrity Verification**: All created archives are verified after packing to detect corruption
- **Vanilla-Style Naming**: Texture archives now use numbered naming like vanilla (`CCMerged - Textures1.ba2`, `CCMerged - Textures2.ba2`)
- **Merged File Detection**: Automatically detects previously merged files and prevents accidental re-merging
- **Comprehensive Error Handling**: Detailed error messages instead of generic "error code 1" failures
- **Administrator Detection**: Warns if running in a protected location without admin rights

### Localization Support

- All original CC STRINGS files are extracted to `Data/Strings` folder
- Original CC plugins (cc*.esl) continue to handle their own localization
- All languages supported (en, de, es, fr, it, ja, pl, pt, ru, zh)
- Prevents "LOOKUP FAILED!" errors

## 📋 Requirements

- Windows 10/11 (64-bit)
- Fallout 4 with Creation Club content
- Creation Kit (for `Archive2.exe`) - [Steam](steam://install/1946160) | [Bethesda.net](https://bethesda.net/en/game/bethesda-launcher)

## 📥 Installation

### Option 1: Download Binary (Recommended)

1. Download `CC-Packer_v1.0.3_Windows.zip` from [Releases](https://github.com/jturnley/CC-Packer/releases)
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
2. **Auto-Detection**: Tool finds Fallout 4 and Archive2.exe automatically
3. **Merge**: Click "Merge CC Archives" button
4. **Wait**: Progress bar shows status (may take 5-15 minutes)
5. **Done**: Launch Fallout 4 and enjoy!

### Manual Path Selection

If auto-detection fails:
- Click "Browse..." to select your Fallout 4 Data folder
- Click "Browse..." to select Archive2.exe location

## 🛡️ Safety & Backup

- All original CC files are automatically backed up to `Data/CC_Backup/`
- Backup is timestamped for easy identification
- Click "Restore Original CC Archives" to undo the merge anytime
- Safe to run multiple times

## 📊 What Gets Merged

| Source Files | Output Archive | Notes |
|-------------|----------------|-------|
| `cc* - Main.ba2` | `CCMerged - Main.ba2` | Compressed, meshes/scripts/etc |
| `cc* - Textures.ba2` | `CCMerged - Textures1.ba2`, `Textures2.ba2`, etc. | Auto-split at 7GB, vanilla naming |
| Sound files (.xwm, .wav, .fuz, .lip) | `CCMerged_Sounds - Main.ba2` | Uncompressed to prevent audio issues |
| STRINGS files | `Data/Strings/*.STRINGS` | Extracted as loose files |

**Output ESL Plugins:**
- `CCMerged.esl` - Light master for main + texture archives
- `CCMerged_Sounds.esl` - Light master for audio archive

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
- **[MGuffin](https://github.com/MGuffin)** - Author of [xTranslator](https://github.com/MGuffin/xTranslator), whose open-source work on Bethesda plugin translation tools helped us understand the STRINGS file format specification used for localization support in CC-Packer (v1.0.3+). xTranslator is an invaluable tool for the modding community.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/jturnley/CC-Packer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jturnley/CC-Packer/discussions)
- **Release Notes**: [View v1.0.2 Release Notes](RELEASE_NOTES_v1.0.2.md)

## 📋 Version History

- **v1.0.3** (November 28, 2025) - Loose STRINGS extraction, separate audio archive, BA2 verification, vanilla naming, comprehensive error handling
- **v1.0.2** (November 26, 2025) - FO4 localization support, enhanced ESL headers
- **v1.0.1** (November 26, 2025) - Smart texture archive splitting, enhanced backup system
- **v1.0.0** (November 26, 2025) - Initial release, basic CC content merging

## 🔗 Related Projects

**[BA2 Manager](https://github.com/jturnley/BA2Manager)** - Full-featured BA2 archive manager for advanced users and modders:
- Conflict detection and resolution
- Batch operations
- MO2 integration
- Custom merging rules

