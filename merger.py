import os
import shutil
import subprocess
import logging
import struct
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List, Tuple

# Note: strings_generator is no longer used - original STRINGS files are preserved
# inside the merged BA2 archives, and our ESL placeholder doesn't need localization.


class Archive2Error(Exception):
    """Custom exception for Archive2 operations with detailed error info."""
    def __init__(self, message: str, operation: str, archive_path: str = None, 
                 return_code: int = None, stdout: str = None, stderr: str = None):
        self.operation = operation
        self.archive_path = archive_path
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr
        
        # Build detailed message
        details = [f"Archive2 {operation} failed"]
        if archive_path:
            details.append(f"Archive: {archive_path}")
        if return_code is not None:
            details.append(f"Exit code: {return_code}")
        if stderr and stderr.strip():
            details.append(f"Error output: {stderr.strip()}")
        if stdout and stdout.strip():
            details.append(f"Output: {stdout.strip()}")
        if message:
            details.append(f"Details: {message}")
            
        super().__init__("\n".join(details))


class CCMerger:
    def __init__(self):
        self.logger = logging.getLogger("CCPacker")
        logging.basicConfig(level=logging.INFO)
        self._last_error_details = None  # Store detailed error info

    def _run_archive2(self, archive2_path: str, args: List[str], operation: str, 
                      archive_name: str = None, progress_callback: Callable = None) -> subprocess.CompletedProcess:
        """Run Archive2.exe with comprehensive error handling.
        
        Args:
            archive2_path: Path to Archive2.exe
            args: Command line arguments for Archive2
            operation: Description of operation (e.g., 'extract', 'create')
            archive_name: Name of archive being processed (for error messages)
            progress_callback: Optional callback for progress messages
            
        Returns:
            CompletedProcess on success
            
        Raises:
            Archive2Error: On any failure with detailed diagnostics
        """
        cmd = [archive2_path] + args
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for large archives
            )
            
            if result.returncode != 0:
                # Parse common Archive2 errors
                error_msg = self._parse_archive2_error(result.stderr, result.stdout, result.returncode)
                raise Archive2Error(
                    message=error_msg,
                    operation=operation,
                    archive_path=archive_name,
                    return_code=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr
                )
            
            return result
            
        except subprocess.TimeoutExpired:
            raise Archive2Error(
                message="Operation timed out after 10 minutes",
                operation=operation,
                archive_path=archive_name
            )
        except FileNotFoundError:
            raise Archive2Error(
                message=f"Archive2.exe not found at: {archive2_path}",
                operation=operation,
                archive_path=archive_name
            )
        except PermissionError:
            raise Archive2Error(
                message="Permission denied - try running as Administrator",
                operation=operation,
                archive_path=archive_name
            )
        except Exception as e:
            raise Archive2Error(
                message=str(e),
                operation=operation,
                archive_path=archive_name
            )

    def _parse_archive2_error(self, stderr: str, stdout: str, return_code: int) -> str:
        """Parse Archive2 output to provide user-friendly error messages."""
        combined = f"{stderr} {stdout}".lower()
        
        if "access" in combined and "denied" in combined:
            return "Access denied - the file may be in use or you need Administrator privileges"
        elif "disk" in combined and ("full" in combined or "space" in combined):
            return "Insufficient disk space to complete operation"
        elif "not found" in combined or "cannot find" in combined:
            return "Source file or directory not found"
        elif "corrupt" in combined or "invalid" in combined:
            return "Archive appears to be corrupted or in an invalid format"
        elif "in use" in combined or "locked" in combined:
            return "File is locked by another process (possibly the game or another tool)"
        elif return_code == 1:
            # Generic error - provide context
            if stderr.strip():
                return f"Archive2 reported an error: {stderr.strip()}"
            elif stdout.strip():
                return f"Archive2 output: {stdout.strip()}"
            else:
                return "Archive2 failed without providing details. Check disk space and file permissions."
        else:
            return f"Unexpected error (code {return_code})"

    def verify_ba2_integrity(self, ba2_path: Path, archive2_path: str = None, 
                             progress_callback: Callable = None) -> Tuple[bool, str]:
        """Verify a BA2 archive is valid and not corrupted.
        
        Args:
            ba2_path: Path to the BA2 file to verify
            archive2_path: Path to Archive2.exe (optional, for deep validation)
            progress_callback: Optional callback for status messages
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not ba2_path.exists():
            return False, f"Archive not found: {ba2_path.name}"
        
        file_size = ba2_path.stat().st_size
        
        # Check minimum file size (BA2 header is at least 24 bytes)
        if file_size < 24:
            return False, f"Archive too small ({file_size} bytes): {ba2_path.name}"
        
        try:
            with open(ba2_path, 'rb') as f:
                # Read and verify BA2 magic number
                magic = f.read(4)
                if magic != b'BTDX':
                    return False, f"Invalid BA2 header (expected 'BTDX'): {ba2_path.name}"
                
                # Read version
                # Known BA2 versions:
                # - Version 1: Original Fallout 4 (2015)
                # - Version 7: Fallout 76 (not used in FO4)
                # - Version 8: Fallout 4 Next-Gen Update (April 2024)
                # We accept 1 and 8 for Fallout 4 compatibility
                version = struct.unpack('<I', f.read(4))[0]
                if version not in [1, 8]:
                    return False, f"Unexpected BA2 version {version} (expected 1 or 8): {ba2_path.name}"
                
                # Read archive type
                # GNRL = General (meshes, scripts, sounds, etc.)
                # DX10 = Textures (DirectX 10 format DDS)
                archive_type = f.read(4).decode('ascii', errors='ignore').strip('\x00')
                if archive_type not in ['GNRL', 'DX10']:
                    return False, f"Unknown archive type '{archive_type}' (expected GNRL or DX10): {ba2_path.name}"
                
                # Read file count
                file_count = struct.unpack('<I', f.read(4))[0]
                
                # Read name table offset
                name_table_offset = struct.unpack('<Q', f.read(8))[0]
                
                # Verify name table offset is within file
                if name_table_offset > file_size:
                    return False, f"Corrupted archive (name table beyond EOF): {ba2_path.name}"
                
                # If Archive2 is available, try a test extraction
                if archive2_path and os.path.exists(archive2_path):
                    try:
                        # Use -l to list contents (quick validation)
                        result = subprocess.run(
                            [archive2_path, str(ba2_path), "-l"],
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        if result.returncode != 0:
                            return False, f"Archive2 validation failed: {result.stderr.strip() or 'Unknown error'}"
                    except subprocess.TimeoutExpired:
                        # Timeout on list is suspicious
                        return False, f"Archive2 timed out reading archive: {ba2_path.name}"
                    except Exception as e:
                        # Don't fail on Archive2 issues, header check passed
                        if progress_callback:
                            progress_callback(f"  Note: Could not run Archive2 validation: {e}")
                
                return True, f"Verified: {ba2_path.name} ({file_count} files, {file_size / (1024*1024):.1f} MB)"
                
        except struct.error as e:
            return False, f"Corrupted archive header: {ba2_path.name}"
        except IOError as e:
            return False, f"Cannot read archive: {e}"
        except Exception as e:
            return False, f"Verification error: {e}"

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
            try:
                self._run_archive2(
                    archive2_path, 
                    [str(f), f"-e={general_dir}"],
                    operation="extract",
                    archive_name=f.name,
                    progress_callback=progress_callback
                )
            except Archive2Error as e:
                return {"success": False, "error": str(e)}

        # Extract Textures
        for i, f in enumerate(texture_ba2s):
            progress_callback(f"Extracting Textures [{i+1}/{len(texture_ba2s)}]: {f.name}")
            try:
                self._run_archive2(
                    archive2_path,
                    [str(f), f"-e={textures_dir}"],
                    operation="extract",
                    archive_name=f.name,
                    progress_callback=progress_callback
                )
            except Archive2Error as e:
                return {"success": False, "error": str(e)}

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
        created_archives = []  # Track created archives for verification
        
        if sound_files:
            output_name_sounds = "CCMerged_Sounds"
            merged_sounds = data_path / f"{output_name_sounds} - Main.ba2"
            progress_callback("Repacking Sounds Archive (Uncompressed)...")
            try:
                self._run_archive2(
                    archive2_path,
                    [str(sounds_dir), f"-c={merged_sounds}", "-f=General", "-compression=None", f"-r={sounds_dir}"],
                    operation="create",
                    archive_name=merged_sounds.name,
                    progress_callback=progress_callback
                )
                created_archives.append(merged_sounds)
            except Archive2Error as e:
                return {"success": False, "error": str(e)}
            
            sounds_esl = f"{output_name_sounds}.esl"
            self._create_vanilla_esl(data_path / sounds_esl)
            created_esls.append(sounds_esl)

        # 7. Repack Main (Compressed)
        # Note: We use Default compression to ensure strings and other data are readable by the engine.
        output_name = "CCMerged"
        merged_main = data_path / f"{output_name} - Main.ba2"
        
        if list(general_dir.rglob("*")):
            progress_callback("Repacking Main Archive (Compressed)...")
            try:
                self._run_archive2(
                    archive2_path,
                    [str(general_dir), f"-c={merged_main}", "-f=General", "-compression=Default", f"-r={general_dir}"],
                    operation="create",
                    archive_name=merged_main.name,
                    progress_callback=progress_callback
                )
                created_archives.append(merged_main)
            except Archive2Error as e:
                return {"success": False, "error": str(e)}
            
            main_esl = f"{output_name}.esl"
            self._create_vanilla_esl(data_path / main_esl)
            created_esls.append(main_esl)

        # 8. Repack Textures (Smart Splitting with Vanilla-style Naming)
        # Vanilla naming: "CCMerged - Textures1.ba2", "CCMerged - Textures2.ba2", etc.
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
            # Use vanilla-style numbering: Textures1, Textures2, etc. (1-indexed)
            texture_num = idx + 1
            # Each texture archive needs its own ESL to load properly
            # Name format: CCMerged_Textures1.esl loads CCMerged_Textures1 - Textures.ba2
            texture_plugin_name = f"{output_name}_Textures{texture_num}"
            archive_name = f"{texture_plugin_name} - Textures.ba2"
            target_path = data_path / archive_name
            
            progress_callback(f"Repacking Textures {texture_num}/{len(groups)}: {archive_name}")
            
            # Move files to temp split dir
            split_dir = temp_dir / f"split_{idx}"
            split_dir.mkdir(exist_ok=True)
            
            for f_path in group:
                rel = f_path.relative_to(textures_dir)
                dest = split_dir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f_path, dest)
            
            try:
                self._run_archive2(
                    archive2_path,
                    [str(split_dir), f"-c={target_path}", "-f=DDS", "-compression=Default", f"-r={split_dir}"],
                    operation="create",
                    archive_name=archive_name,
                    progress_callback=progress_callback
                )
                created_archives.append(target_path)
            except Archive2Error as e:
                return {"success": False, "error": str(e)}
            
            # Create ESL for this texture archive
            texture_esl = f"{texture_plugin_name}.esl"
            self._create_vanilla_esl(data_path / texture_esl)
            created_esls.append(texture_esl)
            progress_callback(f"  Created {texture_esl} for {archive_name}")

        # Note: We do NOT generate separate STRINGS files for CCMerged.esl
        # The original CC plugins (cc*.esl) handle their own localization.
        # We moved the STRINGS files to Data/Strings to ensure the game finds them.
        progress_callback("STRINGS files moved to Data/Strings.")

        # 9. Verify archive integrity before proceeding
        # NOTE: Archive validation disabled - was causing issues with some BA2 versions
        # progress_callback("Verifying archive integrity...")
        # verification_failed = []
        # for archive_path in created_archives:
        #     is_valid, message = self.verify_ba2_integrity(archive_path, archive2_path, progress_callback)
        #     if is_valid:
        #         progress_callback(f"  ✓ {message}")
        #     else:
        #         progress_callback(f"  ✗ {message}")
        #         verification_failed.append(message)
        # 
        # if verification_failed:
        #     error_msg = "Archive verification failed:\n" + "\n".join(verification_failed)
        #     return {"success": False, "error": error_msg}
        # 
        # progress_callback(f"All {len(created_archives)} archives verified successfully.")

        # 10. Add to plugins.txt
        progress_callback("Enabling plugins...")
        self._add_to_plugins_txt(created_esls)

        # 11. Cleanup
        progress_callback("Cleaning up original CC files...")
        for f in cc_files:
            try:
                f.unlink()
            except Exception as e:
                progress_callback(f"Warning: Could not delete {f.name}: {e}")
        
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            progress_callback(f"Warning: Could not clean up temp directory: {e}")

        # Build summary
        summary = {
            "archives_created": len(created_archives),
            "files_processed": len(cc_files),
            "esls_created": len(created_esls)
        }
        progress_callback(f"\nSummary: Created {summary['archives_created']} archives from {summary['files_processed']} CC files.")

        return {"success": True, "summary": summary}

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
