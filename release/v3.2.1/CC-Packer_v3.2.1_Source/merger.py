"""CC Packer - Creation Club Content Merger

This module provides the core functionality for merging Fallout 4 Creation Club content
into optimized archive files. It handles:

- Validation of CC content integrity (checking for complete plugin + BA2 sets)
- Extraction of individual CC archives using BSArch
- Intelligent separation of content types (general, textures, sounds, strings)
- Repacking into optimized merged archives with appropriate compression
- Smart texture splitting to respect game engine limits
- Backup creation and restoration
- Plugin file management (ESL creation and plugins.txt updates)

The merger uses BSArch.exe (bundled with the application) for all BA2 archive
operations and provides comprehensive error handling and progress reporting.

Key Features:
- Content validation to detect incomplete/orphaned CC items
- Automatic cleanup of orphaned content
- Compressed repacking for general content
- Uncompressed repacking for sound files
- Smart texture splitting with vanilla-style naming
- Preservation of STRINGS files as loose files
- Complete backup system with timestamp-based versioning

Classes:
    BSArchError: Custom exception for BSArch operation failures
    CCMerger: Main class that orchestrates all merge/restore operations

Author: CC Packer Development Team
Version: 3.2.1
License: See LICENSE file
"""

import os
import shutil
import subprocess
import logging
import struct
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List, Tuple

# Note: strings_generator is no longer used - original STRINGS files are preserved
# inside the merged BA2 archives, and our ESL placeholder doesn't need localization.


class BSArchError(Exception):
    """Custom exception for BSArch operations with detailed error information.
    
    This exception provides comprehensive error details when BSArch.exe operations
    fail, including return codes, stdout/stderr output, and contextual information
    about what was being attempted.
    
    Attributes:
        operation (str): The operation being performed (e.g., 'pack', 'unpack', 'list')
        archive_path (str): Path to the archive being processed, if applicable
        return_code (int): BSArch exit code, if available
        stdout (str): Standard output from BSArch, if captured
        stderr (str): Error output from BSArch, if captured
    
    The exception message is automatically formatted to include all available
    error details in a human-readable format.
    """
    def __init__(self, message: str, operation: str, archive_path: Optional[str] = None, 
                 return_code: Optional[int] = None, stdout: Optional[str] = None, stderr: Optional[str] = None):
        self.operation = operation
        self.archive_path = archive_path
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr
        
        # Build detailed message
        details = [f"BSArch {operation} failed"]
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
    """Main class for merging and restoring Fallout 4 Creation Club content.
    
    This class provides all functionality needed to:
    - Validate CC content integrity (plugin files + BA2 archives)
    - Detect and handle orphaned/incomplete CC items
    - Merge individual CC archives into optimized combined archives
    - Restore previously backed-up CC content
    - Manage plugin files and game configuration
    
    The merger uses BSArch.exe for all BA2 operations and implements intelligent
    content separation:
    - General content (meshes, scripts, etc.) -> Compressed BA2
    - Textures -> Compressed BA2, split at 7GB to avoid game engine limits
    - Sounds -> Uncompressed BA2 for compatibility
    - STRINGS -> Loose files in Data/Strings (required by game engine)
    
    Merged archives are named with the "CCPacked" prefix (changed from "CCMerged"
    in v2.0) to distinguish them from original CC content. Each archive gets its own
    corresponding ESL file with a matching prefix to ensure the game loads it correctly.
    The merger automatically cleans up legacy v1.x CCMerged files during operations.
    
    Attributes:
        logger: Python logger for internal logging
        _last_error_details: Stores detailed error information from failed operations
        _bsarch_path: Cached path to bsarch.exe to avoid repeated lookups
    
    Thread Safety:
        This class is designed to be used from Qt worker threads. All file
        operations use pathlib.Path for cross-platform compatibility.
    """
    def __init__(self):
        """Initialize the CCMerger instance.
        
        Sets up logging and initializes internal state variables.
        The bsarch.exe path is cached on first use for performance.
        Loads the CCList.txt file containing all known CC items.
        """
        self.logger = logging.getLogger("CCPacker")
        logging.basicConfig(level=logging.INFO)
        self._bsarch_path = None  # Cache bsarch.exe path
        self._cc_list: set[str] = self._load_cc_list()  # Load known CC items

    def _load_cc_list(self) -> set[str]:
        """Load the list of known Creation Club items from CCList.txt.
        
        Reads the CCList.txt file (containing all official CC items) and creates
        a set of filenames for quick lookup. This file is used to validate that
        only actual CC content is detected for merging, preventing files that
        happen to start with 'cc' from being incorrectly included.
        
        The CCList.txt file should be located in the same directory as the
        application script or in the PyInstaller bundle root.
        
        Returns:
            set: Set of CC filenames (e.g., 'ccBGSFO4001-PipBoy.esl')
                Empty set if file cannot be loaded.
        
        Raises:
            Does not raise exceptions - returns empty set if file not found,
            allowing the application to continue with fallback behavior.
        """
        try:
            # Determine the directory containing CCList.txt
            if getattr(sys, 'frozen', False):
                # Running as compiled exe
                base_dir = getattr(sys, '_MEIPASS', Path(sys.executable).parent)
            else:
                # Running as script
                base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
            
            cc_list_path = Path(base_dir) / "CCList.txt"
            
            if not cc_list_path.exists():
                self.logger.warning(f"CCList.txt not found at {cc_list_path}. Using fallback detection.")
                return set()

            cc_set: set[str] = set()
            with open(cc_list_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:  # Skip empty lines
                        cc_set.add(line.lower())  # Store lowercase for case-insensitive matching
            
            self.logger.info(f"Loaded {len(cc_set)} known CC items from CCList.txt")
            return cc_set
            
        except Exception as e:
            self.logger.warning(f"Failed to load CCList.txt: {e}. Using fallback detection.")
            return set()

    def _find_bsarch(self) -> str:
        """Find bsarch.exe bundled with the application.
        
        Searches for bsarch.exe in multiple locations depending on whether
        the application is running as a PyInstaller bundle or as a Python script.
        
        Search locations (in order):
        1. PyInstaller _MEIPASS directory (for bundled exe)
        2. Directory containing the executable
        3. Current working directory
        
        The path is cached after first successful lookup.
        
        Returns:
            str: Absolute path to bsarch.exe
            
        Raises:
            BSArchError: If bsarch.exe cannot be found in any location
        """
        if self._bsarch_path and os.path.exists(self._bsarch_path):
            return self._bsarch_path
        
        # When running as a PyInstaller bundle, files are extracted to a temp directory
        # sys._MEIPASS contains the path to that directory
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            bundle_dir = getattr(sys, '_MEIPASS', Path(sys.executable).parent)
        else:
            # Running as script
            bundle_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        
        possible_paths = [
            Path(bundle_dir) / "bsarch.exe",  # PyInstaller bundle or same dir as script
            Path(sys.executable).parent / "bsarch.exe",  # Same dir as exe
            Path(".") / "bsarch.exe",  # Current directory
        ]
        
        for p in possible_paths:
            if p.exists():
                self._bsarch_path = str(p.resolve())
                return self._bsarch_path
        
        raise BSArchError(
            message="bsarch.exe not found. It should be bundled with CC-Packer.",
            operation="initialization"
        )

    def _run_bsarch(self, args: List[str], operation: str, 
                    archive_name: Optional[str] = None, progress_callback: Optional[Callable[[str], None]] = None,
                    timeout: int = 600, cwd: Optional[Path] = None) -> subprocess.CompletedProcess[str]:
        """Run bsarch.exe with comprehensive error handling.
        
        Central method for all BSArch invocations. Locates the bsarch.exe binary,
        constructs the full command, and executes it as a subprocess. The subprocess
        is launched with CREATE_NO_WINDOW to prevent visible console windows from
        appearing for each operation.
        
        Args:
            args (List[str]): Command line arguments for bsarch (e.g., ['unpack', path, dir])
            operation (str): Human-readable description of the operation being performed
                (e.g., 'unpack', 'pack', 'list'). Used in error messages.
            archive_name (str, optional): Name of the archive being processed. Included
                in error messages for context. Defaults to None.
            progress_callback (Callable, optional): Function accepting a string argument,
                called to report progress messages. Defaults to None.
            timeout (int): Maximum time in seconds to wait for the command to complete.
                Defaults to 600 (10 minutes). Increase for very large archives.
            cwd (Path, optional): Working directory for the subprocess. Critical for
                pack operations where bsarch uses relative paths. Defaults to None
                (inherits parent process working directory).
            
        Returns:
            subprocess.CompletedProcess[str]: The completed process result containing
                stdout, stderr, and returncode on success.
            
        Raises:
            BSArchError: If the process returns a non-zero exit code, times out,
                the executable is not found, or a permission error occurs. The
                exception includes detailed context about the failure.
        """
        bsarch_path = self._find_bsarch()
        cmd = [bsarch_path] + args
        
        try:
            if progress_callback:
                progress_callback(f"  Running: bsarch {' '.join(args[:3])}...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(cwd) if cwd else None,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode != 0:
                error_msg = self._parse_bsarch_error(result.stderr, result.stdout, result.returncode)
                raise BSArchError(
                    message=error_msg,
                    operation=operation,
                    archive_path=archive_name,
                    return_code=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr
                )
            
            return result
            
        except subprocess.TimeoutExpired:
            raise BSArchError(
                message=f"Operation timed out after {timeout} seconds",
                operation=operation,
                archive_path=archive_name
            )
        except FileNotFoundError:
            raise BSArchError(
                message=f"bsarch.exe not found at: {bsarch_path}",
                operation=operation,
                archive_path=archive_name
            )
        except PermissionError:
            raise BSArchError(
                message="Permission denied - try running as Administrator",
                operation=operation,
                archive_path=archive_name
            )
        except Exception as e:
            raise BSArchError(
                message=str(e),
                operation=operation,
                archive_path=archive_name
            )

    def _parse_bsarch_error(self, stderr: str, stdout: str, return_code: int) -> str:
        """Parse BSArch error output to provide user-friendly error messages.
        
        Analyzes the output from bsarch.exe to identify common error conditions
        and provides helpful guidance for resolving them.
        
        Common errors detected:
        - Permission denied -> Suggest running as Administrator
        - File not found -> Suggest checking paths
        - Corrupted archives -> Suggest redownloading from Creations menu
        - Generic failures -> Include raw error output
        
        Args:
            stderr (str): Standard error output from bsarch.exe
            stdout (str): Standard output from bsarch.exe
            return_code (int): Exit code from bsarch.exe
        
        Returns:
            str: User-friendly error message with actionable guidance
        """
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
        elif return_code != 0:
            # Generic error - provide context
            if stderr.strip():
                return f"BSArch reported an error: {stderr.strip()}"
            elif stdout.strip():
                return f"BSArch output: {stdout.strip()}"
            else:
                return "BSArch failed without providing details. Check disk space and file permissions."
        else:
            return f"Unexpected error (code {return_code})"

    def _extract_archive(self, ba2_path: Path, output_dir: Path, 
                        progress_callback: Optional[Callable[[str], None]] = None) -> None:
        """Extract a BA2 archive to the specified directory.
        
        Uses BSArch.exe to unpack the archive. All files are extracted while
        preserving their directory structure.
        
        Args:
            ba2_path (Path): Path to the BA2 archive to extract
            output_dir (Path): Directory where files will be extracted
            progress_callback (Callable, optional): Function to call with progress messages
        
        Raises:
            BSArchError: If extraction fails for any reason
        
        Example:
            >>> merger._extract_archive(
            ...     Path('Data/ccBGSFO4001 - Main.ba2'),
            ...     Path('Data/CC_Temp/General')
            ... )
        """
        # bsarch unpack <archive> [folder] [-mt]
        args = ["unpack", str(ba2_path), str(output_dir), "-mt"]
        self._run_bsarch(args, operation="unpack", archive_name=ba2_path.name, 
                        progress_callback=progress_callback)

    def _pack_general_archive(self, source_dir: Path, output_path: Path,
                              compress: bool = True,
                              progress_callback: Optional[Callable[[str], None]] = None) -> None:
        """Create a general (GNRL) BA2 archive using bsarch.
        
        Args:
            source_dir: Directory containing files to pack
            output_path: Path for the output BA2 file
            compress: Whether to compress the archive (default True)
            progress_callback: Optional callback for progress messages
            
        Raises:
            BSArchError on failure
        """
        # Use '.' as source and set cwd to source_dir to avoid path prefix issues
        # bsarch includes relative path components in archive paths, so we must
        # run from within the source directory
        args = ["pack", ".", str(output_path.resolve()), "-fo4", "-mt"]
        if compress:
            args.append("-z")
        self._run_bsarch(args, operation="pack", archive_name=output_path.name,
                        progress_callback=progress_callback, cwd=source_dir)

    def _pack_texture_archive(self, source_dir: Path, output_path: Path,
                              progress_callback: Optional[Callable[[str], None]] = None) -> None:
        """Pack a texture (DX10) BA2 archive from directory contents.
        
        Creates a DX10-type BA2 archive specifically for texture files (DDS format).
        Texture archives always use compression and must respect the game engine's
        size limitations (handled by caller through texture splitting).
        
        Args:
            source_dir (Path): Directory containing DDS texture files to pack
            output_path (Path): Path where the BA2 archive will be created
            progress_callback (Callable, optional): Function to call with progress messages
        
        Raises:
            BSArchError: If packing fails
        
        Note:
            The archive is created with the '-sse' flag for Fallout 4 compatibility.
            Directory structure is preserved inside the archive.
        """
        # Use '.' as source and set cwd to source_dir to avoid path prefix issues
        # bsarch pack <folder> <archive> -fo4dds -z [-mt]
        # Note: -fo4dds requires -z (compression) per bsarch docs
        args = ["pack", ".", str(output_path.resolve()), "-fo4dds", "-z", "-mt"]
        self._run_bsarch(args, operation="pack", archive_name=output_path.name,
                        progress_callback=progress_callback, cwd=source_dir)

    def _pack_sound_archive(self, source_dir: Path, output_path: Path,
                            progress_callback: Optional[Callable[[str], None]] = None) -> None:
        """Pack an uncompressed general BA2 archive for sound files.
        
        Creates an uncompressed General-type BA2 archive for sound files (.xwm, .wav,
        .fuz, .lip). Sound files must not be compressed to ensure proper playback
        in the game engine.
        
        Args:
            source_dir (Path): Directory containing sound files to pack
            output_path (Path): Path where the BA2 archive will be created
            progress_callback (Callable, optional): Function to call with progress messages
        
        Raises:
            BSArchError: If packing fails
        
        Note:
            Sound files must not be compressed; the archive is packed without
            the -z flag to ensure proper in-game playback.
        """
        # Use '.' as source and set cwd to source_dir to avoid path prefix issues
        # bsarch pack <folder> <archive> -fo4 [-mt]
        # No -z flag = uncompressed
        args = ["pack", ".", str(output_path.resolve()), "-fo4", "-mt"]
        self._run_bsarch(args, operation="pack", archive_name=output_path.name,
                        progress_callback=progress_callback, cwd=source_dir)

    def _get_ba2_file_count(self, ba2_path: Path) -> Tuple[bool, int, str]:
        """Read the file count directly from a BA2 archive's binary header.
        
        Performs a lightweight read of just the first 16 bytes of the BA2 file
        to extract the file count without invoking BSArch. This is faster than
        using BSArch's -list command and is used primarily for post-extraction
        verification.
        
        BA2 Header Layout (first 16 bytes):
            - Bytes 0-3: Magic number ('BTDX')
            - Bytes 4-7: Version (uint32, little-endian)
            - Bytes 8-11: Archive type ('GNRL' or 'DX10')
            - Bytes 12-15: File count (uint32, little-endian)
        
        Args:
            ba2_path (Path): Path to the BA2 archive file to inspect
            
        Returns:
            Tuple[bool, int, str]: A tuple containing:
                - success (bool): True if the header was read successfully
                - file_count (int): Number of files recorded in the archive header
                - error_message (str): Empty string on success, error description on failure
        """
        try:
            with open(ba2_path, 'rb') as f:
                # Read and verify BA2 magic number
                magic = f.read(4)
                if magic != b'BTDX':
                    return False, 0, f"Invalid BA2 header: {ba2_path.name}"
                
                # Skip version (4 bytes) and archive type (4 bytes)
                f.read(8)
                
                # Read file count
                file_count = struct.unpack('<I', f.read(4))[0]
                return True, file_count, ""
                
        except Exception as e:
            return False, 0, f"Error reading BA2 header: {e}"

    def _verify_extraction(self, ba2_path: Path, extract_dir: Path,
                          progress_callback: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
        """Sanity-check that a BA2 extraction produced files on disk.

        Reads the archive header to confirm it reports a non-zero file count,
        then verifies that at least one file exists in the extraction directory.

        Because archives extract cumulatively into a shared directory, this is a
        presence check ("did anything land?"), not a strict per-archive file
        count. If the header can't be read, it degrades to the presence check
        alone rather than failing the merge.
        
        Args:
            ba2_path (Path): Path to the BA2 archive that was extracted
            extract_dir (Path): Directory where files should have been extracted
            progress_callback (Callable, optional): Function for progress messages
        
        Returns:
            Tuple containing:
                - success (bool): True if verification passed
                - message (str): Verification result message
        
        Example:
            >>> ok, msg = merger._verify_extraction(
            ...     Path('Data/ccBGSFO4001 - Main.ba2'),
            ...     Path('Data/CC_Temp/General')
            ... )
            >>> if not ok:
            ...     print(f"Verification failed: {msg}")
        """
        # Use header file count for verification (most reliable)
        success, expected_count, error = self._get_ba2_file_count(ba2_path)
        
        if not success:
            if progress_callback:
                progress_callback(f"  Warning: Could not read archive header: {error}")
            # Can't verify, but don't fail - just check something was extracted.
            # any() short-circuits on the first file rather than walking the whole
            # (cumulatively growing) extraction directory.
            if not any(p.is_file() for p in extract_dir.rglob("*")):
                return False, f"No files extracted from {ba2_path.name}"
            return True, ""
        
        if expected_count == 0:
            if progress_callback:
                progress_callback(f"  Warning: Archive reports 0 files: {ba2_path.name}")
            return True, ""
        
        # For cumulative extraction (multiple archives extract into the same dir)
        # an exact per-archive count isn't possible, so this is only a sanity check
        # that *something* landed on disk. any() short-circuits on the first file
        # instead of walking the entire (growing) directory each call.
        if not any(p.is_file() for p in extract_dir.rglob("*")):
            return False, f"No files extracted from {ba2_path.name}"

        return True, ""

    def _find_cc_plugins(self, data_path: Path) -> List[Path]:
        """Find all Creation Club plugin files in the Data folder.

        Matches files in the Data folder against the authoritative CCList.txt,
        which contains all known official Creation Club plugin filenames. Only
        files present in both the CCList and the Data directory are returned.

        This is the primary method for detecting CC content, as plugin files
        are the canonical identifier for Creation Club items.

        Args:
            data_path (Path): Path to Fallout 4/Data directory

        Returns:
            List[Path]: List of paths to CC plugin files found

        Example:
            >>> plugins = merger._find_cc_plugins(Path('C:/Games/Fallout 4/Data'))
            >>> for p in plugins:
            ...     print(p.name)  # e.g., 'ccBGSFO4001-PipBoy.esl'
        """
        cc_plugins: List[Path] = []

        for cc_filename in self._cc_list:
            plugin_path = data_path / cc_filename
            if plugin_path.exists():
                cc_plugins.append(plugin_path)
        
        return cc_plugins

    def validate_cc_content_integrity(self, data_path: Path, progress_callback: Optional[Callable[[str], None]] = None) -> Tuple[List[str], List[str]]:
        """Check if all CC plugins have their required BA2 archives.
        
        Each Creation Club item consists of a plugin file (.esl/.esp/.esm) and
        two companion BA2 archives:
            - '<base_name> - Main.ba2' (meshes, scripts, sounds, etc.)
            - '<base_name> - Textures.ba2' (DDS texture files)
        
        A CC item is considered "valid" (complete) only if both BA2 files exist.
        A CC item is considered "orphaned" (incomplete) if one or both BA2 files
        are missing — this typically occurs when the game's built-in download
        engine fails to fully download the content.
        
        Orphaned items cannot be safely merged and should be deleted and
        re-downloaded from the Creations menu in Fallout 4.
        
        Args:
            data_path (Path): Path to the Fallout 4/Data directory containing
                CC plugin and BA2 files
            progress_callback (Callable, optional): Function to receive progress
                messages. Each CC item is reported with a checkmark (valid) or
                cross (orphaned) along with which archives are missing.
            
        Returns:
            Tuple[List[str], List[str]]: A tuple containing:
                - valid_cc_names (List[str]): Base names of complete CC items
                  (e.g., 'ccBGSFO4001-PipBoy(Pip-BoyPack01)')
                - orphaned_cc_names (List[str]): Base names of incomplete CC items
                  that are missing one or both BA2 archives
        """
        cc_plugins = self._find_cc_plugins(data_path)
        
        if progress_callback:
            progress_callback(f"Found {len(cc_plugins)} Creation Club plugin(s).")
        
        valid_cc: List[str] = []
        orphaned_cc: List[str] = []
        
        for plugin in cc_plugins:
            # Extract base name (remove extension)
            base_name = plugin.stem  # e.g., 'ccBGSFO4001-PipBoy(Pip-BoyPack01)'
            
            # Check for main BA2 (e.g., 'ccBGSFO4001-PipBoy(Pip-BoyPack01) - Main.ba2')
            main_ba2 = data_path / f"{base_name} - Main.ba2"
            
            # Check for texture BA2 (e.g., 'ccBGSFO4001-PipBoy(Pip-BoyPack01) - Textures.ba2')
            texture_ba2 = data_path / f"{base_name} - Textures.ba2"
            
            if main_ba2.exists() and texture_ba2.exists():
                valid_cc.append(base_name)
                if progress_callback:
                    progress_callback(f"  ✓ {plugin.name} - Complete")
            else:
                orphaned_cc.append(base_name)
                missing: List[str] = []
                if not main_ba2.exists():
                    missing.append("Main")
                if not texture_ba2.exists():
                    missing.append("Textures")
                if progress_callback:
                    progress_callback(f"  ✗ {plugin.name} - Missing: {', '.join(missing)}")
        
        return valid_cc, orphaned_cc

    def _remove_from_fallout4_ccc(self, fo4_path: Path, base_names: List[str], progress_callback: Optional[Callable[[str], None]] = None) -> None:
        """Remove plugin entries from Fallout4.ccc for successfully deleted CC items.

        Args:
            fo4_path: Path to the Fallout 4 installation directory (parent of Data).
            base_names: Plugin stems to remove (e.g. ['ccBGSFO4001-PipBoy(Black)']).
            progress_callback: Optional function to receive status messages.
        """
        ccc_path = fo4_path / "Fallout4.ccc"
        if not ccc_path.exists():
            return

        target_stems = {n.lower() for n in base_names}

        try:
            lines = ccc_path.read_text(encoding='utf-8').splitlines(keepends=True)
            kept: List[str] = []
            removed: List[str] = []
            for line in lines:
                stem = Path(line.strip()).stem.lower()
                if stem in target_stems:
                    removed.append(line.strip())
                else:
                    kept.append(line)
            if removed:
                ccc_path.write_text(''.join(kept), encoding='utf-8')
                for entry in removed:
                    if progress_callback:
                        progress_callback(f"  Removed from Fallout4.ccc: {entry}")
        except Exception as e:
            if progress_callback:
                progress_callback(f"  Warning: Could not update Fallout4.ccc: {e}")

    def delete_orphaned_cc_content(self, data_path: Path, orphaned_cc_names: List[str], progress_callback: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
        """Delete all files associated with orphaned (incomplete) CC content.
        
        Removes plugin files and any remaining BA2 archives for CC items that
        were identified as incomplete by validate_cc_content_integrity(). This
        cleans up partially-downloaded content that would otherwise cause issues
        or instability in the game.
        
        For each orphaned CC base name, the following files are deleted if they
        exist:
            - '<base_name>.esl', '<base_name>.esp', '<base_name>.esm' (plugin files)
            - '<base_name> - Main.ba2' (main archive, if present)
            - '<base_name> - Textures.ba2' (texture archive, if present)
        
        The method is fault-tolerant: if some files cannot be deleted (e.g., due
        to permissions), it continues with the remaining files and reports all
        failures in the return message.
        
        Args:
            data_path (Path): Path to the Fallout 4/Data directory
            orphaned_cc_names (List[str]): List of base CC names to delete
                (e.g., ['ccBGSFO4001-PipBoy(Pip-BoyPack01)']). These should come
                from the orphaned list returned by validate_cc_content_integrity().
            progress_callback (Callable, optional): Function to receive per-file
                deletion status messages.
            
        Returns:
            Tuple[bool, str]: A tuple containing:
                - success (bool): True if all deletions succeeded, False if any failed
                - message (str): Summary of deletions performed and any failures
        """
        if not orphaned_cc_names:
            return True, "No orphaned content to delete."

        deleted_count = 0
        failed_deletions: List[str] = []
        fully_deleted_names: List[str] = []

        for base_name in orphaned_cc_names:
            files_to_delete: List[Path] = []

            # Plugin files (esl, esp, esm)
            for ext in ['.esl', '.esp', '.esm']:
                plugin_file = data_path / f"{base_name}{ext}"
                if plugin_file.exists():
                    files_to_delete.append(plugin_file)

            # BA2 archives (Main and Textures)
            main_ba2 = data_path / f"{base_name} - Main.ba2"
            texture_ba2 = data_path / f"{base_name} - Textures.ba2"
            if main_ba2.exists():
                files_to_delete.append(main_ba2)
            if texture_ba2.exists():
                files_to_delete.append(texture_ba2)

            # Delete all found files, tracking per-item success
            item_failed = False
            for file_path in files_to_delete:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    if progress_callback:
                        progress_callback(f"  Deleted: {file_path.name}")
                except Exception as e:
                    item_failed = True
                    failed_deletions.append(f"{file_path.name}: {e}")
                    if progress_callback:
                        progress_callback(f"  Failed to delete {file_path.name}: {e}")

            if not item_failed:
                fully_deleted_names.append(base_name)

        # Remove successfully deleted plugins from Fallout4.ccc
        if fully_deleted_names:
            self._remove_from_fallout4_ccc(data_path.parent, fully_deleted_names, progress_callback)

        if failed_deletions:
            return False, f"Deleted {deleted_count} files, but {len(failed_deletions)} deletions failed:\n" + "\n".join(failed_deletions)

        return True, f"Successfully deleted {deleted_count} orphaned CC files."

    def merge_cc_content(self, fo4_path: str, valid_cc: List[str], progress_callback: Callable[[str], None]) -> Dict[str, Any]:
        """Main merge operation - combines Creation Club archives into optimized merged archives.

        This is the core method that orchestrates the complete merge process:

        1. **Cleanup**: Removes old CCPacked files from previous merges
        2. **Backup**: Creates timestamped backup of all original CC files
        3. **Extraction**: Extracts all CC archives to temporary directories
        4. **Content Separation**:
           - STRINGS files -> Moved to Data/Strings as loose files (required by game)
           - Sound files (.xwm, .wav, .fuz, .lip) -> Separated for uncompressed packing
           - Textures (.dds) -> Kept separate for DX10 archive type
           - General content -> Everything else
        5. **Repacking**:
           - Sounds: Uncompressed General BA2 (for compatibility)
           - Main: Compressed General BA2 (meshes, scripts, etc.)
           - Textures: Compressed DX10 BA2(s), split at 7GB to respect game limits
        6. **Plugin Creation**: Creates minimal ESL files for each merged archive
        7. **Game Configuration**: Updates plugins.txt to enable the ESL files
        8. **Cleanup**: Deletes original CC files and temporary directories
        
        Archive Naming Convention (v2.0+):
        - CCPacked_Sounds.esl + CCPacked_Sounds - Main.ba2 (if sound files exist)
        - CCPacked_Main.esl + CCPacked_Main - Main.ba2 (general content)
        - CCPacked_Main_Textures1.esl + CCPacked_Main_Textures1 - Textures.ba2 (first texture batch)
        - CCPacked_Main_Textures2.esl + CCPacked_Main_Textures2 - Textures.ba2 (second batch, if needed)
        - etc.
        
        Legacy v1.x naming used CCMerged prefix, which is cleaned up during merge/restore
        to support seamless upgrades.
        
        Performance Benefits:
        - Reduces plugin count from potentially dozens to 2-5 plugins
        - Improves load times by consolidating archives
        - Reduces game startup time and memory usage
        - Maintains full compatibility with all CC content
        
        Args:
            fo4_path: Path to Fallout 4 installation directory
            valid_cc: Pre-validated list of CC item base names (plugin stems) to merge.
                Caller is responsible for ensuring all items have both Main and Textures
                BA2 files present (use validate_cc_content_integrity beforehand).
            progress_callback: Callback function(str) for progress updates

        Returns:
            Dict containing:
                On success:
                    - 'success': True
                    - 'summary': Dict with 'archives_created', 'files_processed', 'esls_created'
                On failure:
                    - 'success': False
                    - 'error': Error message string

        Example:
            >>> result = merger.merge_cc_content(
            ...     'C:/Games/Fallout 4',
            ...     valid_cc_names,
            ...     lambda msg: print(msg)
            ... )
            >>> if result['success']:
            ...     print(f\"Created {result['summary']['archives_created']} archives\")
        """
        data_path = Path(fo4_path) / "Data"
        backup_dir = data_path / "CC_Backup"
        temp_dir = data_path / "CC_Temp"
        
        if not data_path.exists():
            return {"success": False, "error": "Data folder not found."}

        # Verify bsarch is available
        try:
            bsarch_path = self._find_bsarch()
            progress_callback(f"Using BSArch: {bsarch_path}")
        except BSArchError as e:
            return {"success": False, "error": str(e)}

        progress_callback(f"Merging {len(valid_cc)} Creation Club item(s)...")

        # Build list of BA2 files from valid CC plugins
        cc_files: List[Path] = []
        for base_name in valid_cc:
            main_ba2 = data_path / f"{base_name} - Main.ba2"
            texture_ba2 = data_path / f"{base_name} - Textures.ba2"
            cc_files.append(main_ba2)
            cc_files.append(texture_ba2)

        # Check if merged files already exist (optional cleanup warning)
        existing_merged = list(data_path.glob("CCPacked*.ba2"))
        if existing_merged:
            progress_callback(f"Warning: Found {len(existing_merged)} previously merged archive(s). These will be replaced.")

        # 2. Clean up old merged files and their ESLs
        progress_callback("Cleaning up old merged files...")
        # Clean up both v2.0 (CCPacked) and v1.x (CCMerged) files
        for pattern in ["CCPacked*.*", "CCMerged*.*"]:
            for f in data_path.glob(pattern):
                try:
                    f.unlink()
                except Exception as e:
                    progress_callback(f"Warning: Could not delete {f.name}: {e}")

        # Also clean up old STRINGS files
        strings_dir = data_path / "Strings"
        if strings_dir.exists():
            for pattern in ["CCPacked*.*", "CCMerged*.*"]:
                for f in strings_dir.glob(pattern):
                    try:
                        f.unlink()
                    except Exception as e:
                        progress_callback(f"Warning: Could not delete STRINGS file {f.name}: {e}")

        # 3. Backup - Back up BA2 files only (plugin files remain in place)
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

        main_ba2s: List[Path] = [f for f in cc_files if "texture" not in f.name.lower()]
        texture_ba2s: List[Path] = [f for f in cc_files if "texture" in f.name.lower()]

        # Extract Main archives with verification after each
        for i, f in enumerate(main_ba2s):
            progress_callback(f"Extracting Main [{i+1}/{len(main_ba2s)}]: {f.name}")
            try:
                self._extract_archive(f, general_dir, progress_callback)
                
                # Verify extraction completed successfully
                verify_ok, verify_error = self._verify_extraction(f, general_dir, progress_callback)
                if not verify_ok:
                    return {"success": False, "error": f"Verification failed for {f.name}: {verify_error}"}
                progress_callback(f"  ✓ Verified: {f.name}")
                
            except BSArchError as e:
                return {"success": False, "error": str(e)}

        # Extract Textures with verification after each
        for i, f in enumerate(texture_ba2s):
            progress_callback(f"Extracting Textures [{i+1}/{len(texture_ba2s)}]: {f.name}")
            try:
                self._extract_archive(f, textures_dir, progress_callback)
                
                # Verify extraction completed successfully
                verify_ok, verify_error = self._verify_extraction(f, textures_dir, progress_callback)
                if not verify_ok:
                    return {"success": False, "error": f"Verification failed for {f.name}: {verify_error}"}
                progress_callback(f"  ✓ Verified: {f.name}")
                
            except BSArchError as e:
                return {"success": False, "error": str(e)}

        # Handle Strings - Move to Data/Strings (Force loose files)
        progress_callback("Moving STRINGS files to Data/Strings...")
        target_strings_dir = data_path / "Strings"
        target_strings_dir.mkdir(exist_ok=True)
        
        moved_strings: List[str] = []
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
        sound_files: List[Path] = []
        
        progress_callback("Separating sound files...")
        for f in general_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() in ['.xwm', '.wav', '.fuz', '.lip']:
                rel_path = f.relative_to(general_dir)
                target_path = sounds_dir / rel_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(f, target_path)
                sound_files.append(target_path)
        
        created_esls: List[str] = []

        # 6. Repack Sounds (Uncompressed)
        created_archives: List[Path] = []  # Track created archives for verification
        
        if sound_files:
            output_name_sounds = "CCPacked_Sounds"
            merged_sounds = data_path / f"{output_name_sounds} - Main.ba2"
            progress_callback("Repacking Sounds Archive (Uncompressed)...")
            try:
                self._pack_sound_archive(sounds_dir, merged_sounds, progress_callback)
                created_archives.append(merged_sounds)
            except BSArchError as e:
                return {"success": False, "error": str(e)}
            
            sounds_esl = f"{output_name_sounds}.esl"
            self._create_vanilla_esl(data_path / sounds_esl)
            created_esls.append(sounds_esl)

        # 7. Repack Main (Compressed)
        output_name = "CCPacked_Main"
        merged_main = data_path / f"{output_name} - Main.ba2"
        
        if any(general_dir.rglob("*")):
            progress_callback("Repacking Main Archive (Compressed)...")
            try:
                self._pack_general_archive(general_dir, merged_main, compress=True, 
                                          progress_callback=progress_callback)
                created_archives.append(merged_main)
            except BSArchError as e:
                return {"success": False, "error": str(e)}
            
            main_esl = f"{output_name}.esl"
            self._create_vanilla_esl(data_path / main_esl)
            created_esls.append(main_esl)

        # 8. Repack Textures (Smart Splitting with Vanilla-style Naming)
        texture_files: List[Tuple[Path, int]] = []
        for f in textures_dir.rglob("*"):
            if f.is_file():
                texture_files.append((f, f.stat().st_size))
        
        # Split textures by 7GB uncompressed (typically compresses to ~3.5GB)
        MAX_SIZE = int(7.0 * 1024 * 1024 * 1024) 
        
        groups: List[List[Path]] = []
        current_group: List[Path] = []
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
            texture_plugin_name = f"{output_name}_Textures{texture_num}"
            archive_name = f"{texture_plugin_name} - Textures.ba2"
            target_path = data_path / archive_name
            
            progress_callback(f"Repacking Textures {texture_num}/{len(groups)}: {archive_name}")
            
            # If only one group, pack directly from textures_dir to avoid redundant copy
            if len(groups) == 1:
                pack_dir = textures_dir
            else:
                # Multiple groups: copy files to temp split dir
                pack_dir = temp_dir / f"split_{idx}"
                pack_dir.mkdir(exist_ok=True)
                
                for f_path in group:
                    rel = f_path.relative_to(textures_dir)
                    dest = pack_dir / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f_path, dest)
            
            try:
                self._pack_texture_archive(pack_dir, target_path, progress_callback)
                created_archives.append(target_path)
            except BSArchError as e:
                return {"success": False, "error": str(e)}
            
            # Create ESL for this texture archive
            texture_esl = f"{texture_plugin_name}.esl"
            self._create_vanilla_esl(data_path / texture_esl)
            created_esls.append(texture_esl)
            progress_callback(f"  Created {texture_esl} for {archive_name}")

        # 9. Add to plugins.txt
        progress_callback("Enabling plugins...")
        self._add_to_plugins_txt(created_esls)

        # 10. Cleanup - Delete original CC BA2 files only (plugin files remain)
        progress_callback("Cleaning up original CC BA2 files...")
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

    def restore_backup(self, fo4_path: str, progress_callback: Callable[[str], None]) -> Dict[str, Any]:
        """Restore Creation Club content from the most recent backup.
        
        This method reverses a merge operation by:
        1. **Finding Latest Backup**: Locates the most recent timestamped backup
        2. **Removing Merged Content**:
           - Deletes all CCPacked BA2 archives
           - Deletes CCPacked ESL plugin files
           - Cleans up CCPacked STRINGS files
           - Removes extracted STRINGS files that were part of merged content
        3. **Restoring Original Files**:
           - Copies original CC BA2 archives back to Data folder
           - (Plugin files are not restored because they are never deleted during merge)
        4. **Updating Game Configuration**: Removes CCPacked entries from plugins.txt
        5. **Cleanup**: Deletes old backups, keeping only the most recent
        
        The restore process is safe and will always keep at least one backup.
        Users can merge again after restoring to re-create optimized archives.
        
        Args:
            fo4_path: Path to Fallout 4 installation directory
            progress_callback: Callback function(str) for progress updates
            
        Returns:
            Dict containing:
                On success:
                    - 'success': True
                On failure:
                    - 'success': False
                    - 'error': Error message string
        
        Example:
            >>> result = merger.restore_backup(
            ...     'C:/Games/Fallout 4',
            ...     lambda msg: print(msg)
            ... )
            >>> if result['success']:
            ...     print("CC content restored successfully")
        """
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

        # Delete merged files (both v2.0 CCPacked and v1.x CCMerged)
        merged_esls: List[str] = []
        for pattern in ["CCPacked*.*", "CCMerged*.*"]:
            for f in data_path.glob(pattern):
                if f.suffix.lower() == ".esl":
                    merged_esls.append(f.name)
                f.unlink()

        # Delete merged STRINGS files
        strings_dir = data_path / "Strings"
        if strings_dir.exists():
            for pattern in ["CCPacked*.*", "CCMerged*.*"]:
                for f in strings_dir.glob(pattern):
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
        for f in backup_files:
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

    def _get_plugins_txt(self) -> Optional[Path]:
        """Get the path to Fallout 4's plugins.txt configuration file.
        
        The plugins.txt file lives in the user's local application data directory
        at: %LOCALAPPDATA%/Fallout4/plugins.txt
        
        This file controls which plugin files (.esl, .esp, .esm) the game loads
        on startup. Entries prefixed with '*' are enabled. CC Packer adds its
        merged ESL entries here during merge and removes them during restore.
        
        Returns:
            Path: Absolute path to plugins.txt, or None if the LOCALAPPDATA
                environment variable is not set (should not occur on Windows).
        """
        local_app_data = os.environ.get('LOCALAPPDATA')
        if not local_app_data:
            return None
        return Path(local_app_data) / "Fallout4" / "plugins.txt"

    def _add_to_plugins_txt(self, esl_names: List[str]) -> None:
        """Add ESL plugin entries to plugins.txt for game to load them.
        
        Modifies the game's plugins.txt file (in AppData/Local/Fallout4) to include
        the merged archive ESL files. This ensures the game loads the merged BA2
        archives when it starts.
        
        If plugins.txt doesn't exist, it's created. Entries are only added if they
        don't already exist (idempotent operation).
        
        Args:
            esl_names: List of ESL filenames to add (e.g., ['CCPacked_Main.esl'])
        
        Note:
            The method handles both cases where plugins.txt has a UTF-8 BOM and
            where it doesn't, preserving the existing format.
        """
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

    def _remove_from_plugins_txt(self, esl_names: List[str]) -> None:
        """Remove ESL plugin entries from plugins.txt.
        
        Removes the merged archive ESL entries from the game's plugins.txt file
        during restore operations. This prevents the game from trying to load
        archives that no longer exist.
        
        If plugins.txt doesn't exist or doesn't contain the specified entries,
        the method safely returns without error (idempotent operation).
        
        Args:
            esl_names: List of ESL filenames to remove (e.g., ['CCPacked_Main.esl'])
        
        Note:
            Preserves UTF-8 BOM if it exists in the original file.
        """
        plugins_txt = self._get_plugins_txt()
        if not plugins_txt or not plugins_txt.exists():
            return

        try:
            with open(plugins_txt, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [l.strip() for l in f.readlines()]
        except:
            return

        new_lines: List[str] = []
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

    def _create_vanilla_esl(self, path: Path) -> None:
        """Create a minimal ESL plugin file for merged archives.
        
        Creates a dummy ESL (Elder Scrolls Light) plugin file that serves to
        make the game engine load the associated BA2 archive. The ESL contains
        only a minimal header and no actual game data.
        
        Fallout 4 requires a plugin file to exist for any BA2 archive to be loaded.
        These placeholder ESLs ensure our merged archives are recognized by the game.
        
        The ESL format includes:
        - TES4 header record
        - Version number (1.0)
        - Minimal flags for ESL format
        - Dummy master file reference
        - Author and description fields
        
        Args:
            path: Path where the ESL file should be created
        
        Note:
            The created ESL does not need STRINGS files because it contains no
            localized text. All actual strings remain in the original loose files
            or within the merged archives.
        """
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
