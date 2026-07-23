"""CC Packer - Main GUI Application

This module provides the graphical user interface for CC Packer, a tool that merges
Fallout 4 Creation Club content into optimized archive files to improve game performance
and reduce plugin count.

The application uses PyQt6 for the GUI and runs merge/restore operations in background
threads to keep the interface responsive.

Classes:
    MergeWorker: Background thread worker for merge operations
    RestoreWorker: Background thread worker for restore operations
    MainWindow: Main application window with UI and controls

Author: CC Packer Development Team
Version: 3.2.0
License: See LICENSE file
"""

import sys
import os
import re
import ctypes
from pathlib import Path
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QTextEdit, QFileDialog, QMessageBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from merger import CCMerger


class MergeWorker(QThread):
    """Background worker thread for performing CC content merge operations.
    
    This worker runs the merge process in a separate thread to prevent the UI from
    freezing during lengthy archive extraction and repacking operations.
    
    Signals:
        progress (str): Emitted during merge to report progress messages
        finished (bool, str): Emitted when merge completes with success status and message
    
    Attributes:
        merger (CCMerger): The merger instance that performs the actual work
        fo4_path (str): Path to the Fallout 4 installation directory
        valid_cc (List[str]): Pre-validated list of CC base names to merge
    """
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, merger: CCMerger, fo4_path: str, valid_cc: List[str]) -> None:
        """Initialize the merge worker.

        Args:
            merger (CCMerger): Instance of CCMerger to use for operations
            fo4_path (str): Path to Fallout 4 installation directory
            valid_cc (List[str]): Pre-validated list of CC base names to merge
        """
        super().__init__()
        self.merger = merger
        self.fo4_path = fo4_path
        self.valid_cc = valid_cc

    def run(self):
        """Execute the merge operation in the background thread.
        
        This method calls the merger's merge_cc_content() method and emits signals
        to report progress and completion status back to the main thread.
        
        Emits:
            progress: Progress messages during the merge operation
            finished: Final result with (success: bool, message: str)
        """
        try:
            result = self.merger.merge_cc_content(self.fo4_path, self.valid_cc, self.progress.emit)
            if result['success']:
                self.finished.emit(True, "Merge completed successfully!")
            else:
                self.finished.emit(False, result.get('error', 'Unknown error'))
        except Exception as e:
            self.finished.emit(False, str(e))


class RestoreWorker(QThread):
    """Background worker thread for performing backup restore operations.
    
    This worker runs the restore process in a separate thread to prevent UI freezing
    when restoring previously backed-up Creation Club files.
    
    Signals:
        progress (str): Emitted during restore to report progress messages
        finished (bool, str): Emitted when restore completes with success status and message
    
    Attributes:
        merger (CCMerger): The merger instance that performs the actual work
        fo4_path (str): Path to the Fallout 4 installation directory
    """
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, merger: CCMerger, fo4_path: str) -> None:
        """Initialize the restore worker.
        
        Args:
            merger (CCMerger): Instance of CCMerger to use for operations
            fo4_path (str): Path to Fallout 4 installation directory
        """
        super().__init__()
        self.merger = merger
        self.fo4_path = fo4_path

    def run(self):
        """Execute the restore operation in the background thread.
        
        This method calls the merger's restore_backup() method and emits signals
        to report progress and completion status back to the main thread.
        
        Emits:
            progress: Progress messages during the restore operation
            finished: Final result with (success: bool, message: str)
        """
        try:
            result = self.merger.restore_backup(self.fo4_path, self.progress.emit)
            if result['success']:
                self.finished.emit(True, "Restore completed successfully!")
            else:
                self.finished.emit(False, result.get('error', 'Unknown error'))
        except Exception as e:
            self.finished.emit(False, str(e))


class MainWindow(QMainWindow):
    """Main application window for CC Packer.
    
    This class provides the primary user interface for CC Packer, including:
    - Auto-detection of Fallout 4 installation path
    - Display of current merge/backup status
    - Merge and restore operation controls
    - Real-time log output display
    - Handling of orphaned Creation Club content
    - Administrator privilege detection and warnings
    
    The window automatically detects the Fallout 4 installation using registry
    keys and common installation paths, and displays the current state of
    Creation Club content (merged vs. unmerged).
    
    Attributes:
        merger (CCMerger): Instance of CCMerger for performing operations
        fo4_input (QLineEdit): Input field for Fallout 4 path
        merge_btn (QPushButton): Button to start merge operation
        restore_btn (QPushButton): Button to start restore operation
        log_output (QTextEdit): Text area for displaying log messages
        worker (QThread): Currently running background worker thread
        _pending_merge_after_restore (bool): Internal flag that is set to True
            when a restore operation is triggered as part of the automatic
            "restore then repack" workflow. When True, on_finished() will
            automatically start a merge after the restore completes successfully.
    """
    
    def __init__(self):
        """Initialize the main window.
        
        Sets up the UI components, initializes the merger instance, and
        attempts to auto-detect the Fallout 4 installation path.
        """
        super().__init__()
        self.setGeometry(100, 100, 800, 600)
        self.merger = CCMerger()
        self.worker = None
        self._pending_merge_after_restore = False
        self.init_ui()
        self.detect_paths()

    def init_ui(self):
        """Initialize and configure the user interface.
        
        Creates all UI components including:
        - Application header
        - Fallout 4 directory selection controls
        - Merge and Restore buttons
        - Log output text area
        
        The UI uses PyQt6 layouts for responsive design.
        """
        self.setWindowTitle("CC Packer v3.2.0")
        self.setMinimumSize(600, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Header
        header = QLabel("CC Packer")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # FO4 Path
        layout.addWidget(QLabel("Fallout 4 Directory:"))
        fo4_layout = QHBoxLayout()
        self.fo4_input = QLineEdit()
        fo4_btn = QPushButton("Browse")
        fo4_btn.clicked.connect(self.browse_fo4)  # type: ignore
        fo4_layout.addWidget(self.fo4_input)
        fo4_layout.addWidget(fo4_btn)
        layout.addLayout(fo4_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.merge_btn = QPushButton("Merge CC Content")
        self.merge_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.merge_btn.clicked.connect(self.start_merge)  # type: ignore
        
        self.restore_btn = QPushButton("Restore Backup")
        self.restore_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px;")
        self.restore_btn.clicked.connect(self.start_restore)  # type: ignore
        
        btn_layout.addWidget(self.merge_btn)
        btn_layout.addWidget(self.restore_btn)
        layout.addLayout(btn_layout)

        # Log
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

    def log(self, message: str) -> None:
        """Append a message to the log output display.
        
        Args:
            message (str): The message to display in the log
        """
        self.log_output.append(message)

    def _disable_buttons(self):
        """Disable merge and restore buttons during operation."""
        self.merge_btn.setEnabled(False)
        self.restore_btn.setEnabled(False)

    def _check_existing_backup(self, fo4_path: str) -> Dict[str, Any]:
        """Check for existing backups and Creation Club file states.

        Scans the Data folder to identify:
        - Previously merged CCPacked archives
        - Unmerged CC content (validated against CCList.txt)
        - Available backups in CC_Backup folder

        This information is used to determine the current state and enable/disable
        appropriate UI controls.

        Args:
            fo4_path (str): Path to Fallout 4 installation directory

        Returns:
            dict: Dictionary containing:
                - 'has_ccmerged' (bool): True if CCPacked files exist (variable name is legacy)
                - 'has_other_cc' (bool): True if unmerged CC BA2 files exist
                - 'backup_count' (int): Number of existing backups
                - 'ccmerged_files' (list): Names of CCPacked files found (variable name is legacy)
                - 'other_cc_files' (list): Names of unmerged CC Main BA2 files found
        """
        data_path = Path(fo4_path) / "Data"
        backup_dir = data_path / "CC_Backup"
        
        # Default empty result
        result: Dict[str, Any] = {
            'has_ccmerged': False,
            'has_other_cc': False,
            'backup_count': 0,
            'ccmerged_files': [],
            'other_cc_files': []
        }
        
        if not data_path.exists():
            return result
        
        # Find CCPacked (merged) archives using explicit prefix
        ccmerged_files = [f.name for f in data_path.glob("CCPacked*.ba2")]

        # Find unmerged CC BA2 files by checking CCList entries
        other_cc_files = []
        for cc_filename in self.merger._cc_list:
            base_name = Path(cc_filename).stem
            main_ba2 = data_path / f"{base_name} - Main.ba2"
            if main_ba2.exists():
                other_cc_files.append(main_ba2.name)
        
        # Count backups
        backup_count = 0
        if backup_dir.exists():
            backup_count = len([d for d in backup_dir.iterdir() if d.is_dir()])
        
        return {
            'has_ccmerged': len(ccmerged_files) > 0,
            'has_other_cc': len(other_cc_files) > 0,
            'backup_count': backup_count,
            'ccmerged_files': ccmerged_files,
            'other_cc_files': other_cc_files
        }

    def _show_merge_status(self, fo4_path: str) -> None:
        """Display the current merge/backup status and update button states.
        
        Analyzes the current state of CC content and backups, then:
        - Logs status messages to the output display
        - Enables/disables the merge button based on current state
        - Enables/disables the restore button based on backup availability
        - Sets tooltips to explain button states
        
        States handled:
        - All files merged (disable merge button)
        - Mixed merged/unmerged files (enable merge with warning)
        - No merged files (normal state, merge enabled)
        - Backups available (enable restore)
        - No backups (disable restore)
        
        Args:
            fo4_path (str): Path to Fallout 4 installation directory
        """
        status = self._check_existing_backup(fo4_path)
        
        # Build status message for log
        if status['has_ccmerged']:
            merged_count = len(status['ccmerged_files'])
            self.log(f"Found {merged_count} merged archive(s): {', '.join(status['ccmerged_files'][:2])}")
            if merged_count > 2:
                self.log(f"  ... and {merged_count - 2} more")
        
        if status['has_other_cc']:
            other_count = len(status['other_cc_files'])
            self.log(f"Found {other_count} unmerged CC file(s)")
        
        if status['backup_count'] > 0:
            self.log(f"Found {status['backup_count']} backup(s)")
        
        # Determine merge button state
        if status['has_ccmerged'] and not status['has_other_cc']:
            # Only merged files - can't merge
            self.merge_btn.setEnabled(False)
            self.merge_btn.setToolTip("All Creation Club files are already merged.\nRestore backup to merge additional files.")
            self.log("⚠ All CC files are merged. Use 'Restore Backup' to add more files.")
        elif status['has_ccmerged'] and status['has_other_cc']:
            # Mixed - can merge but should restore first
            self.merge_btn.setEnabled(True)
            self.merge_btn.setToolTip("Unmerged CC files detected alongside merged files.\nConsider restoring backup first.")
            self.log("⚠ Mixed merged and unmerged files detected!")
        else:
            # No merged files - normal state
            self.merge_btn.setEnabled(True)
            self.merge_btn.setToolTip("Merge Creation Club files")
        
        # Restore button state
        if status['backup_count'] > 0:
            self.restore_btn.setEnabled(True)
        else:
            self.restore_btn.setEnabled(False)
            self.restore_btn.setToolTip("No backups available")

    def _is_admin(self):
        """Check if the application is running with administrator privileges.
        
        Uses Windows API to determine if the current process has admin rights.
        This is important for detecting potential permission issues when Fallout 4
        is installed in protected directories like Program Files.
        
        Returns:
            bool: True if running as administrator, False otherwise
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False

    def _is_protected_path(self, path: str) -> bool:
        """Check if a path is in a Windows-protected location.
        
        Determines if the given path is under a Windows-protected directory
        such as Program Files, Program Files (x86), or Windows.
        
        Args:
            path (str): Path to check
        
        Returns:
            bool: True if path is in a protected location, False otherwise
        """
        protected_prefixes = [
            os.environ.get('ProgramFiles', r'C:\Program Files'),
            os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)'),
            os.environ.get('SystemRoot', r'C:\Windows'),
        ]
        path_lower = path.lower()
        return any(path_lower.startswith(p.lower()) for p in protected_prefixes if p)

    def _check_elevation_needed(self, path: str) -> bool:
        """Warn user if elevation may be required for the given path.
        
        If Fallout 4 is installed in a protected location and CC Packer is not
        running as administrator, displays a warning dialog advising the user
        to run as administrator to avoid permission errors.
        
        Args:
            path (str): Path to Fallout 4 installation directory
        
        Returns:
            bool: True if warning was displayed, False otherwise
        """
        if self._is_protected_path(path) and not self._is_admin():
            QMessageBox.warning(
                self,
                "Administrator Rights May Be Required",
                f"Fallout 4 is installed in a protected location:\n\n"
                f"{path}\n\n"
                "You may need to run CC-Packer as Administrator to modify files.\n\n"
                "Right-click CCPacker.exe and select 'Run as administrator'."
            )
            self.log("⚠ Warning: FO4 is in a protected location. Run as Administrator if you encounter errors.")
            return True
        return False

    def detect_paths(self):
        """Auto-detect Fallout 4 installation path using multiple methods.
        
        Attempts to locate Fallout 4 using the following methods in order:
        1. Bethesda registry keys (both 64-bit and 32-bit)
        2. Steam library folders (by parsing libraryfolders.vdf)
        3. Common hardcoded installation paths
        
        If a valid path is found, it's automatically populated in the UI and
        the current merge status is displayed. Also checks if administrator
        privileges may be required.
        
        The detection is automatic and runs when the application starts.
        """
        # Try to detect FO4 via registry
        import winreg
        
        fo4_path = None
        
        # Method 1: Check Bethesda's Fallout 4 registry key directly
        try:
            for reg_path in [
                r"SOFTWARE\WOW6432Node\Bethesda Softworks\Fallout4",
                r"SOFTWARE\Bethesda Softworks\Fallout4"
            ]:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                        path = winreg.QueryValueEx(key, "Installed Path")[0]
                        if path and os.path.exists(path):
                            fo4_path = path.rstrip("\\")
                            break
                except (FileNotFoundError, OSError):
                    continue
        except Exception as e:
            self.log(f"Registry detection error: {e}")
        
        # Method 2: Fallback - check Steam library folders
        if not fo4_path:
            try:
                steam_path = None
                for reg_path in [r"SOFTWARE\WOW6432Node\Valve\Steam", r"SOFTWARE\Valve\Steam"]:
                    try:
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                            steam_path = winreg.QueryValueEx(key, "InstallPath")[0]
                            break
                    except (FileNotFoundError, OSError):
                        continue
                
                if steam_path:
                    vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
                    if os.path.exists(vdf_path):
                        library_paths = [steam_path]
                        with open(vdf_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            paths = re.findall(r'"path"\s+"([^"]+)"', content)
                            library_paths.extend(paths)
                        
                        for lib_path in library_paths:
                            potential_fo4 = os.path.join(lib_path, "steamapps", "common", "Fallout 4")
                            if os.path.exists(potential_fo4):
                                fo4_path = potential_fo4
                                break
            except Exception as e:
                self.log(f"Steam detection error: {e}")
        
        # Method 3: Fallback to common hardcoded paths
        if not fo4_path:
            common_paths = [
                r"C:\Program Files (x86)\Steam\steamapps\common\Fallout 4",
                r"C:\Program Files\Steam\steamapps\common\Fallout 4",
                r"D:\SteamLibrary\steamapps\common\Fallout 4",
                r"E:\SteamLibrary\steamapps\common\Fallout 4",
            ]
            for path in common_paths:
                if os.path.exists(path):
                    fo4_path = path
                    break
        
        # Apply the detected path
        if fo4_path:
            self.fo4_input.setText(fo4_path)
            self.log(f"Auto-detected Fallout 4 at: {fo4_path}")
            try:
                self._show_merge_status(fo4_path)
                self._check_elevation_needed(fo4_path)
            except Exception as e:
                self.log(f"Error checking status: {e}")
        else:
            self.log("Fallout 4 not found. Please browse to select.")

    def browse_fo4(self):
        """Open directory browser dialog for manual Fallout 4 path selection.
        
        Allows the user to manually select the Fallout 4 installation directory
        if auto-detection fails or if they want to work with a different installation.
        
        After selection, updates the UI with the merge status and checks for
        elevation requirements.
        """
        path = QFileDialog.getExistingDirectory(self, "Select Fallout 4 Directory")
        if path:
            self.fo4_input.setText(path)
            self._show_merge_status(path)
            self._check_elevation_needed(path)

    def _handle_orphaned_cc_content(self, fo4_path: str, orphaned_names: List[str]) -> Optional[str]:
        """Show warning dialog for orphaned CC content and handle user choice.
        
        When CC content validation detects incomplete items (plugins missing their
        BA2 archives), this method displays a rich-text warning dialog explaining
        the situation and offering three options:
        
        1. **Delete and Cancel**: Deletes the orphaned files, then stops so the
           user can re-download the content from the Creations menu in-game.
        2. **Delete and Continue**: Deletes the orphaned files and proceeds with
           merging the remaining valid CC content.
        3. **Cancel Without Changes**: Makes no modifications and aborts the merge.
        
        The dialog includes a clickable link to the CC Packer Nexus Mods page
        for more information about the orphaned content issue.
        
        If deletion is selected but fails (e.g., due to permissions), an error
        dialog is shown and the method returns None to abort the merge.
        
        Args:
            fo4_path (str): Path to the Fallout 4 installation directory. Used
                to locate the Data folder for file deletion.
            orphaned_names (List[str]): List of CC base names (without extension)
                that are missing required BA2 archive files.
            
        Returns:
            Optional[str]: One of the following:
                - 'continue': Orphaned content was successfully deleted; caller
                  should re-validate and proceed with merging.
                - 'quit': User chose to stop (with or without deletion).
                - None: An error occurred during deletion or user cancelled;
                  caller should abort the merge.
        """
        
        # Format the list of orphaned items with HTML for better visibility
        orphaned_list = "<br>".join([f"&nbsp;&nbsp;&nbsp;&nbsp;<b>{name}</b>" for name in orphaned_names])
        
        # Create custom message box with clickable link
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Incomplete Creation Club Content Detected")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        
        # Build message with rich text for clickable link
        message = (
            "The following Creation Club items are missing their required BA2 archive files:<br><br>"
            f"{orphaned_list}<br><br>"
            "You may continue, but these items will not function and may cause instability "
            "or crashing until you have deleted and re-downloaded them from the Creations Shop "
            "on the Fallout 4 main menu.<br><br>"
            "Note that this is not an issue with CC Packer; it is a known issue with the "
            "download engine built into the game.<br><br>"
            "I can automatically delete the affected incomplete CC items for you, I can delete them "
            "and continue packing the remaining files, or you can cancel packing to do the deletions "
            "and re-download them yourself.<br><br>"
            'See the <a href="https://www.nexusmods.com/fallout4/mods/98589?tab=description">CC Packer main page</a> '
            "on Nexus Mods for more information."
        )
        
        msg_box.setText(message)
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        
        # Add custom buttons
        delete_quit_btn = msg_box.addButton("Delete Orphaned CC Content And Cancel Packing", QMessageBox.ButtonRole.DestructiveRole)
        delete_continue_btn = msg_box.addButton("Delete Orphaned CC Content and Continue", QMessageBox.ButtonRole.AcceptRole)
        _quit_btn = msg_box.addButton("Make No Changes and Cancel Packing Now", QMessageBox.ButtonRole.RejectRole)
        
        msg_box.exec()
        clicked = msg_box.clickedButton()
        
        # Handle user choice
        data_path = Path(fo4_path) / "Data"
        
        if clicked == delete_quit_btn or clicked == delete_continue_btn:
            # Delete orphaned content
            self.log("Deleting orphaned Creation Club content...")
            success, message = self.merger.delete_orphaned_cc_content(
                data_path, orphaned_names, self.log
            )
            
            if not success:
                QMessageBox.critical(
                    self,
                    "Deletion Failed",
                    f"Failed to delete some orphaned content:\n\n{message}\n\n"
                    "You may need to run CC Packer as Administrator."
                )
                return None
            
            self.log(message)
            
            if clicked == delete_quit_btn:
                self.log("User chose to quit after deletion.")
                return 'quit'
            else:
                self.log("Continuing with merge after deletion...")
                return 'continue'
        
        else:  # quit_btn
            self.log("User chose to quit without deletion.")
            return 'quit'

    def start_merge(self):
        """Initiate the Creation Club content merge process.
        
        This method orchestrates the complete merge workflow:
        1. Validates the Fallout 4 path
        2. Checks current backup/merge status
        3. Handles mixed merged/unmerged file states
        4. Validates CC content integrity (checks for orphaned files)
        5. Presents orphaned content warning dialog if needed
        6. Allows user to clean up orphaned content
        7. Launches the merge worker thread if validation passes
        
        The actual merge operation runs in a background thread (MergeWorker)
        to keep the UI responsive during lengthy archive operations.
        
        User flow for orphaned content:
        - If incomplete CC items are found, user can choose to:
          a) Delete orphaned content and quit
          b) Delete orphaned content and continue merging
          c) Quit without changes
        - After deletion, re-validates to ensure cleanup succeeded
        - Only proceeds with merge if validation passes
        """
        fo4 = self.fo4_input.text()

        if not fo4 or not os.path.exists(fo4):
            QMessageBox.warning(self, "Error", "Invalid Fallout 4 path.")
            return

        data_path = Path(fo4) / "Data"

        # Check for mixed content FIRST - if CCPacked archives exist alongside
        # unmerged CC files, we must restore backup before validating integrity.
        # Otherwise, validation will see all CC plugins as "orphaned" because
        # their individual BA2 files were packed into CCPacked archives.
        status = self._check_existing_backup(fo4)
        
        # Case 1: Only merged files exist - can't merge
        if status['has_ccmerged'] and not status['has_other_cc']:
            QMessageBox.information(
                self,
                "All CC Content Already Packed",
                "All CC Content is already packed!"
            )
            return
        
        # Case 2: Mixed merged and unmerged files - restore first, then re-merge
        if status['has_ccmerged'] and status['has_other_cc']:
            self.log("Mixed CC content detected. Restoring backup and repacking all CC items...")
            self._pending_merge_after_restore = True
            self.start_restore()
            return
        
        # Now validate CC content integrity (safe to do after mixed-content check)
        self.log("Checking Creation Club content integrity...")
        valid_cc, orphaned_cc = self.merger.validate_cc_content_integrity(data_path, self.log)
        
        # Handle orphaned content if found
        if orphaned_cc:
            result = self._handle_orphaned_cc_content(fo4, orphaned_cc)
            
            if result == 'quit':
                # User chose to quit
                return
            elif result == 'continue':
                # Orphaned content was deleted, refresh validation
                self.log("Re-validating after deletion...")
                valid_cc, orphaned_cc = self.merger.validate_cc_content_integrity(data_path, self.log)
                
                if orphaned_cc:
                    QMessageBox.critical(
                        self,
                        "Validation Failed",
                        "Orphaned content still detected after deletion. Please check manually."
                    )
                    return
                
                if not valid_cc:
                    QMessageBox.information(
                        self,
                        "No Content to Merge",
                        "No valid Creation Club content remains after cleanup."
                    )
                    return
            else:
                # Deletion failed — critical dialog already shown by _handle_orphaned_cc_content
                self.log("Merge cancelled: could not delete all orphaned CC content.")
                return
        
        # Verify we have content to merge
        if not valid_cc:
            QMessageBox.information(
                self,
                "No Content Found",
                "No Creation Club content found to merge."
            )
            return

        self._disable_buttons()
        self.log("Starting merge process...")
        
        self.worker = MergeWorker(self.merger, fo4, valid_cc)
        self.worker.progress.connect(self.log)  # type: ignore
        self.worker.finished.connect(self.on_finished)  # type: ignore
        self.worker.start()

    def start_restore(self):
        """Initiate the backup restore process.
        
        Restores the most recent backup of Creation Club files, reversing a previous
        merge operation. The restore includes:
        - Original individual CC BA2 archives
        - Plugin files (.esl/.esp/.esm) are not restored because they are never deleted
        - Removal of merged CCPacked archives
        - Updating plugins.txt
        
        The actual restore operation runs in a background thread (RestoreWorker)
        to keep the UI responsive.
        
        Validates the Fallout 4 path before starting the restore.
        """
        fo4 = self.fo4_input.text()
        if not fo4 or not os.path.exists(fo4):
            QMessageBox.warning(self, "Error", "Invalid Fallout 4 path.")
            return

        self._disable_buttons()
        self.log("Starting restore process...")

        self.worker = RestoreWorker(self.merger, fo4)
        self.worker.progress.connect(self.log)  # type: ignore
        self.worker.finished.connect(self.on_finished)  # type: ignore
        self.worker.start()

    def on_finished(self, success: bool, message: str) -> None:
        """Handle completion of background worker operations.
        
        Called when merge or restore worker completes. Re-enables UI buttons
        and displays appropriate success or error message to the user.
        
        If a restore operation completed successfully and a merge was pending
        (from the restore+repack workflow), automatically starts the merge.
        
        Args:
            success (bool): True if operation succeeded, False if it failed
            message (str): Success or error message to display
        """
        self.merge_btn.setEnabled(True)
        self.restore_btn.setEnabled(True)
        
        if success:
            # Check if this was a restore operation with pending merge
            if self._pending_merge_after_restore:
                self._pending_merge_after_restore = False
                self.log(f"Restore complete: {message}")
                self.log("Now starting merge of all CC content...")
                # Don't show success dialog yet, proceed to merge
                self.start_merge()
            else:
                QMessageBox.information(self, "Success", message)
                self.log(f"DONE: {message}")
        else:
            # Clear pending merge on error
            self._pending_merge_after_restore = False
            QMessageBox.critical(self, "Error", message)
            self.log(f"ERROR: {message}")

if __name__ == "__main__":
    """Application entry point.
    
    Creates the Qt application, displays the main window, and starts the
    event loop. The application continues running until the user closes
    the window or quits the application.
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
