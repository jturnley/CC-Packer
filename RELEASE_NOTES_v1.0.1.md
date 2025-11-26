# CC-Packer v1.0.1 Release Notes

## Sound Fix Update

This release addresses a critical issue where sound files (music, voice lines, sound effects) were not playing correctly in-game after merging.

### Changes

- **Sound File Separation**: The tool now automatically detects sound files (`.xwm`, `.wav`, `.fuz`) during the extraction process.
- **Uncompressed Packing**: Sound files are now packed into a separate, uncompressed archive (`CCMerged_Sounds - Main.ba2`). This ensures the Fallout 4 engine can stream them correctly without playback issues.
- **Automatic Plugin Handling**: A new dummy ESL plugin (`CCMerged_Sounds.esl`) is automatically created and added to `plugins.txt` to load the new sound archive.
- **Seamless Restore**: The restore function has been updated to automatically clean up the new sound archives and plugins.

### Upgrading

1. Run the new `CCPacker.exe`.
2. If you have a previous merge active, click **Restore Backup** first.
3. Click **Merge CC Content** to create the new merged archives with the sound fix.
