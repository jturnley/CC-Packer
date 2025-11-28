import os
import shutil
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Note: strings_generator is no longer used - original STRINGS files are preserved
# inside the merged BA2 archives, and our ESL placeholder doesn't need localization.

class CCMerger:
    def __init__(self):
        self.logger = logging.getLogger("CCPacker")
        logging.basicConfig(level=logging.INFO)

    def merge_cc_content(self, fo4_path, archive2_path, progress_callback):
        data_path = Path(fo4_path) / "Data"
        backup_dir = data_path / "CC_Backup"
        temp_dir = data_path / "CC_Temp"
        
        if not data_path.exists():
            return {"success": False, "error": "Data folder not found."}

        # 1. Identify CC Files (exclude CCMerged files created by this tool)
        all_cc_files = list(data_path.glob("cc*.ba2"))
        # Filter out any CCMerged archives to prevent re-packing previously merged content
        cc_files = [f for f in all_cc_files if not f.name.lower().startswith("ccmerged")]
        
        if not cc_files:
            if all_cc_files:
                return {"success": False, "error": "Only previously merged (CCMerged) archives found. No new CC files to merge."}
            else:
                return {"success": False, "error": "No Creation Club (cc*.ba2) files found."}

        progress_callback(f"Found {len(cc_files)} CC archives.")

        # Check if merged files already exist (optional cleanup warning)
        existing_merged = list(data_path.glob("CCMerged*.ba2"))
        if existing_merged:
            progress_callback(f"Warning: Found {len(existing_merged)} previously merged archive(s). These will be replaced.")

        # 2. Clean up old merged files and their ESLs
        progress_callback("Cleaning up old merged files...")
        for f in data_path.glob("CCMerged*.*"):
            try:
                f.unlink()
            except Exception as e:
                progress_callback(f"Warning: Could not delete {f.name}: {e}")

        # Also clean up old STRINGS files
        strings_dir = data_path / "Strings"
        if strings_dir.exists():
            for f in strings_dir.glob("CCMerged*.*"):
                try:
                    f.unlink()
                except Exception as e:
                    progress_callback(f"Warning: Could not delete STRINGS file {f.name}: {e}")

        # 3. Backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_backup = backup_dir / timestamp
        current_backup.mkdir(parents=True, exist_ok=True)
        
        progress_callback(f"Backing up files to {current_backup}...")
        for f in cc_files:
            shutil.copy2(f, current_backup / f.name)

        # 4. Extract
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir()
        
        general_dir = temp_dir / "General"
        textures_dir = temp_dir / "Textures"
        general_dir.mkdir()
        textures_dir.mkdir()

        main_ba2s = [f for f in cc_files if "texture" not in f.name.lower()]
        texture_ba2s = [f for f in cc_files if "texture" in f.name.lower()]

        # Extract Main
        for i, f in enumerate(main_ba2s):
            progress_callback(f"Extracting Main [{i+1}/{len(main_ba2s)}]: {f.name}")
            subprocess.run([archive2_path, str(f), f"-e={general_dir}"], check=True, capture_output=True)

        # Extract Textures
        for i, f in enumerate(texture_ba2s):
            progress_callback(f"Extracting Textures [{i+1}/{len(texture_ba2s)}]: {f.name}")
            subprocess.run([archive2_path, str(f), f"-e={textures_dir}"], check=True, capture_output=True)

        # Handle Strings - Move to Data/Strings (Force loose files)
        progress_callback("Moving STRINGS files to Data/Strings...")
        target_strings_dir = data_path / "Strings"
        target_strings_dir.mkdir(exist_ok=True)
        
        moved_strings = []
        # Recursively find all string files
        for f in general_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() in ['.strings', '.dlstrings', '.ilstrings']:
                target_file = target_strings_dir / f.name
                try:
                    # Use copy instead of copy2 to update timestamp (helps with archive invalidation)
                    shutil.copy(f, target_file)
                    f.unlink() # Remove from temp dir so it's not packed into the archive
                    moved_strings.append(f.name)
                except Exception as e:
                    progress_callback(f"Warning: Failed to move {f.name}: {e}")

        if moved_strings:
            progress_callback(f"Moved {len(moved_strings)} string files to Data/Strings")
            with open(current_backup / "moved_strings.txt", "w", encoding="utf-8") as f:
                for s in moved_strings:
                    f.write(f"{s}\n")
        else:
            progress_callback("Warning: No STRINGS files found in extracted content.")

        # 5. Separate Sounds (Uncompressed)
        sounds_dir = temp_dir / "Sounds"
        sounds_dir.mkdir(exist_ok=True)
        sound_files = []
        
        progress_callback("Separating sound files...")
        for f in general_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() in ['.xwm', '.wav', '.fuz', '.lip']:
                rel_path = f.relative_to(general_dir)
                target_path = sounds_dir / rel_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(f, target_path)
                sound_files.append(target_path)
        
        created_esls = []

        # 6. Repack Sounds (Uncompressed)
        if sound_files:
            output_name_sounds = "CCMerged_Sounds"
            merged_sounds = data_path / f"{output_name_sounds} - Main.ba2"
            progress_callback("Repacking Sounds Archive (Uncompressed)...")
            subprocess.run([archive2_path, str(sounds_dir), f"-c={merged_sounds}", "-f=General", "-compression=None", f"-r={sounds_dir}"], check=True, capture_output=True)
            
            sounds_esl = f"{output_name_sounds}.esl"
            self._create_vanilla_esl(data_path / sounds_esl)
            created_esls.append(sounds_esl)

        # 7. Repack Main (Compressed)
        # Note: We use Default compression to ensure strings and other data are readable by the engine.
        output_name = "CCMerged"
        merged_main = data_path / f"{output_name} - Main.ba2"
        
        if list(general_dir.rglob("*")):
            progress_callback("Repacking Main Archive (Compressed)...")
            subprocess.run([archive2_path, str(general_dir), f"-c={merged_main}", "-f=General", "-compression=Default", f"-r={general_dir}"], check=True, capture_output=True)
            
            main_esl = f"{output_name}.esl"
            self._create_vanilla_esl(data_path / main_esl)
            created_esls.append(main_esl)

        # 8. Repack Textures (Smart Splitting)
        texture_files = []
        for f in textures_dir.rglob("*"):
            if f.is_file():
                texture_files.append((f, f.stat().st_size))
        
        # Split textures by 7GB uncompressed (typically compresses to ~3.5GB)
        MAX_SIZE = int(7.0 * 1024 * 1024 * 1024) 
        
        groups = []
        current_group = []
        current_size = 0
        
        for f_path, f_size in texture_files:
            if current_size + f_size > MAX_SIZE and current_group:
                groups.append(current_group)
                current_group = []
                current_size = 0
            current_group.append(f_path)
            current_size += f_size
        if current_group:
            groups.append(current_group)

        for idx, group in enumerate(groups):
            suffix = "" if idx == 0 else f"_Part{idx+1}"
            archive_name = f"{output_name}{suffix} - Textures.ba2"
            target_path = data_path / archive_name
            
            progress_callback(f"Repacking Textures Part {idx+1}/{len(groups)}...")
            
            # Move files to temp split dir
            split_dir = temp_dir / f"split_{idx}"
            split_dir.mkdir(exist_ok=True)
            
            for f_path in group:
                rel = f_path.relative_to(textures_dir)
                dest = split_dir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f_path, dest)
            
            subprocess.run([archive2_path, str(split_dir), f"-c={target_path}", "-f=DDS", "-compression=Default", f"-r={split_dir}"], check=True, capture_output=True)
            
            # Create ESL for this part
            esl_name = f"{output_name}{suffix}.esl"
            self._create_vanilla_esl(data_path / esl_name)
            created_esls.append(esl_name)

        # Note: We do NOT generate separate STRINGS files for CCMerged.esl
        # The original CC plugins (cc*.esl) handle their own localization.
        # We moved the STRINGS files to Data/Strings to ensure the game finds them.
        progress_callback("STRINGS files moved to Data/Strings.")

        # 9. Add to plugins.txt
        progress_callback("Enabling plugins...")
        self._add_to_plugins_txt(created_esls)

        # 10. Cleanup
        progress_callback("Cleaning up...")
        for f in cc_files:
            f.unlink()
        shutil.rmtree(temp_dir)

        return {"success": True}

    def restore_backup(self, fo4_path, progress_callback):
        data_path = Path(fo4_path) / "Data"
        backup_dir = data_path / "CC_Backup"
        
        if not backup_dir.exists():
            return {"success": False, "error": "No backup folder found."}
            
        # Find most recent backup
        backups = sorted([d for d in backup_dir.iterdir() if d.is_dir()], key=lambda x: x.stat().st_mtime, reverse=True)
        if not backups:
            return {"success": False, "error": "No backups found."}
            
        latest_backup = backups[0]
        progress_callback(f"Restoring from {latest_backup.name}...")

        # Delete merged files
        merged_esls = []
        for f in data_path.glob("CCMerged*.*"):
            if f.suffix.lower() == ".esl":
                merged_esls.append(f.name)
            f.unlink()

        # Delete merged STRINGS files
        strings_dir = data_path / "Strings"
        if strings_dir.exists():
            for f in strings_dir.glob("CCMerged*.*"):
                try:
                    f.unlink()
                    progress_callback(f"Removed STRINGS file: {f.name}")
                except Exception as e:
                    progress_callback(f"Warning: Could not delete {f.name}: {e}")

            # Clean up extracted STRINGS files
            manifest_file = latest_backup / "moved_strings.txt"
            if manifest_file.exists():
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        moved_strings = [l.strip() for l in f.readlines()]
                    
                    progress_callback("Cleaning up extracted STRINGS files...")
                    for s in moved_strings:
                        s_path = strings_dir / s
                        if s_path.exists():
                            try:
                                s_path.unlink()
                            except Exception as e:
                                progress_callback(f"Warning: Could not delete {s}: {e}")
                except Exception as e:
                    progress_callback(f"Warning: Could not read moved_strings.txt: {e}")

        # Remove from plugins.txt
        self._remove_from_plugins_txt(merged_esls)

        # Restore files
        backup_files = list(latest_backup.glob("*"))
        for i, f in enumerate(backup_files):
            if f.name == "moved_strings.txt":
                continue
            shutil.copy2(f, data_path / f.name)

        # Clean up old backups, keeping only the most recent one
        if len(backups) > 1:
            progress_callback("Cleaning up old backups...")
            for old_backup in backups[1:]:
                try:
                    shutil.rmtree(old_backup)
                    progress_callback(f"Removed old backup: {old_backup.name}")
                except Exception as e:
                    progress_callback(f"Warning: Could not remove {old_backup.name}: {e}")
            
        return {"success": True}

    def _get_plugins_txt(self):
        local_app_data = os.environ.get('LOCALAPPDATA')
        if not local_app_data:
            return None
        return Path(local_app_data) / "Fallout4" / "plugins.txt"

    def _add_to_plugins_txt(self, esl_names):
        plugins_txt = self._get_plugins_txt()
        if not plugins_txt or not plugins_txt.parent.exists():
            return

        if not plugins_txt.exists():
            lines = []
        else:
            try:
                with open(plugins_txt, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = [l.strip() for l in f.readlines()]
            except:
                return

        modified = False
        for esl in esl_names:
            entry = f"*{esl}"
            if entry not in lines and esl not in lines:
                lines.append(entry)
                modified = True
        
        if modified:
            try:
                with open(plugins_txt, 'w', encoding='utf-8') as f:
                    f.write("\n".join(lines))
            except Exception as e:
                self.logger.error(f"Failed to write plugins.txt: {e}")

    def _remove_from_plugins_txt(self, esl_names):
        plugins_txt = self._get_plugins_txt()
        if not plugins_txt or not plugins_txt.exists():
            return

        try:
            with open(plugins_txt, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [l.strip() for l in f.readlines()]
        except:
            return

        new_lines = []
        modified = False
        for line in lines:
            clean_line = line.lstrip("*")
            if clean_line in esl_names:
                modified = True
                continue
            new_lines.append(line)

        if modified:
            try:
                with open(plugins_txt, 'w', encoding='utf-8') as f:
                    f.write("\n".join(new_lines))
            except Exception as e:
                self.logger.error(f"Failed to write plugins.txt: {e}")

    def _create_vanilla_esl(self, path):
        # Create vanilla-compatible ESL matching Bethesda's format exactly
        # Reference: https://en.uesp.net/wiki/Skyrim_Mod:Mod_File_Format/TES4
        data = bytearray()
        
        # TES4 Record Header
        data.extend(b'TES4')
        size_placeholder = len(data)
        data.extend(b'\x00\x00\x00\x00')  # Record size (placeholder)
        
        # Flags for ESL (Light Master):
        # 0x00000001 = Master file (ESM)
        # 0x00000200 = Light Master (ESL)
        # Combined: 0x201 = Master + Light Master
        # Note: We do NOT set the Localized flag (0x80) because our ESL is a placeholder
        # with no records. The original CC plugins handle their own localization via
        # STRINGS files that are preserved in the merged BA2.
        flags = 0x00000001 | 0x00000200  # 0x201
        data.extend(flags.to_bytes(4, 'little'))
        
        data.extend(b'\x00\x00\x00\x00')  # Form ID (unused for TES4)
        data.extend(b'\x00\x00\x00\x00')  # Timestamp & Version Control
        data.extend(b'\x00\x00\x00\x00')  # Form Version & Unknown
        
        # HEDR subrecord (Header) - Required
        data.extend(b'HEDR')
        data.extend(b'\x0c\x00')  # Data size (12 bytes)
        data.extend(b'\x00\x00\x80\x3f')  # Version 1.0 (float)
        data.extend(b'\x00\x00\x00\x00')  # Number of records
        data.extend(b'\x00\x00\x00\x00')  # Next object ID
        
        # CNAM subrecord (Creator name) - null-terminated string
        creator = b'CC-Packer\x00'
        data.extend(b'CNAM')
        data.extend(len(creator).to_bytes(2, 'little'))
        data.extend(creator)
        
        # SNAM subrecord (Summary/Description) - null-terminated string
        summary = b'Merged Creation Club Content - Localization Ready\x00'
        data.extend(b'SNAM')
        data.extend(len(summary).to_bytes(2, 'little'))
        data.extend(summary)
        
        # INTV subrecord (Internal Version) - used for tagified strings count
        # Setting to 0 indicates no tagified master strings
        data.extend(b'INTV')
        data.extend(b'\x04\x00')  # Data size (4 bytes)
        data.extend(b'\x00\x00\x00\x00')  # Tagified string count = 0
        
        # Update record size (total size - 24-byte TES4 header)
        # TES4 header is: 4 (type) + 4 (size) + 4 (flags) + 4 (formid) + 4 (timestamp) + 4 (version)
        record_size = len(data) - 24
        data[size_placeholder:size_placeholder+4] = record_size.to_bytes(4, 'little')
        
        with open(path, 'wb') as f:
            f.write(data)
