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
- Each Creation Club item = 1 plugin
- With 70+ CC items, you're left with only ~180 slots for mods
- Game performance degrades with many small BA2 archives

### The Solution

- Merges all CC archives into 4-6 unified files
- Reduces plugin count from 70+ to just 1 master plugin
- Improves game loading times by 10-30%
- Frees up plugin slots for your favorite mods
- Prevents "Brown Face" bug through automatic texture splitting
- **NEW**: Full localization support for enhanced compatibility
- **STRINGS Generation**: Automatic extraction and merging of localized text

## 🆕 What's New in v1.0.3?

### STRINGS File Preservation

The v1.0.3+ update properly handles STRINGS files for localization:

- **Original STRINGS Preserved**: All original CC STRINGS files (e.g., `ccSWKFO4001-AstronautPowerArmor_en.STRINGS`) are preserved inside the merged BA2 archives
- **Plugin Localization Works**: The original CC plugins (cc*.esl) continue to handle their own localization
- **No Additional Files Needed**: The game automatically finds STRINGS files inside BA2 archives
- **All Languages Supported**: STRINGS files for all languages (en, de, es, fr, it, ja, pl, pt, ru, zh) are preserved

This approach ensures compatibility with all language settings and prevents "LOOKUP FAILED!" errors.

## 📋 Requirements

- Windows 10/11 (64-bit)
- Fallout 4 with Creation Club content
- Creation Kit (for `Archive2.exe`) - [Free download from Bethesda.net](https://bethesda.net/en/game/bethesda-launcher)

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

- `cc*-Main.ba2` → `CCMerged-Main.ba2`
- `cc*-Textures.ba2` → `CCMerged-Textures.ba2` (auto-split if >3GB)
- `cc*-Sounds.ba2` → `CCMerged-Sounds.ba2` (uncompressed, v1.0.2+)
- `cc*-Geometry.ba2` → `CCMerged-Geometry.ba2`
- `cc*-Voices_en.ba2` → `CCMerged-Voices_en.ba2`
- All other archive types merged appropriately
- Each merged archive gets an ESL plugin with proper localization metadata

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

- **v1.0.2** (November 26, 2025) - FO4 localization support, enhanced ESL headers
- **v1.0.1** - Smart texture archive splitting, enhanced backup system
- **v1.0.0** - Initial release, basic CC content merging

## 🔗 Related Projects

**[BA2 Manager](https://github.com/jturnley/BA2Manager)** - Full-featured BA2 archive manager for advanced users and modders:
- Conflict detection and resolution
- Batch operations
- MO2 integration
- Custom merging rules

