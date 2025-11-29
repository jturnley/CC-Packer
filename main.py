import sys
import os
import logging
import webbrowser
import ctypes
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QTextEdit, QFileDialog, QMessageBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from merger import CCMerger

class MergeWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, merger, fo4_path, archive2_path):
        super().__init__()
        self.merger = merger
        self.fo4_path = fo4_path
        self.archive2_path = archive2_path

    def run(self):
        try:
            result = self.merger.merge_cc_content(self.fo4_path, self.archive2_path, self.progress.emit)
            if result['success']:
                self.finished.emit(True, "Merge completed successfully!")
            else:
                self.finished.emit(False, result.get('error', 'Unknown error'))
        except Exception as e:
            self.finished.emit(False, str(e))

class RestoreWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, merger, fo4_path):
        super().__init__()
        self.merger = merger
        self.fo4_path = fo4_path

    def run(self):
        try:
            result = self.merger.restore_backup(self.fo4_path, self.progress.emit)
            if result['success']:
                self.finished.emit(True, "Restore completed successfully!")
            else:
                self.finished.emit(False, result.get('error', 'Unknown error'))
        except Exception as e:
            self.finished.emit(False, str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.merger = CCMerger()
        self.init_ui()
        self.detect_paths()

    def init_ui(self):
        self.setWindowTitle("CC Packer v1.0.6")
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
        fo4_btn.clicked.connect(self.browse_fo4)
        fo4_layout.addWidget(self.fo4_input)
        fo4_layout.addWidget(fo4_btn)
        layout.addLayout(fo4_layout)

        # Archive2 Path
        layout.addWidget(QLabel("Archive2.exe Path:"))
        a2_layout = QHBoxLayout()
        self.a2_input = QLineEdit()
        a2_btn = QPushButton("Browse")
        a2_btn.clicked.connect(self.browse_archive2)
        a2_layout.addWidget(self.a2_input)
        a2_layout.addWidget(a2_btn)
        layout.addLayout(a2_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.merge_btn = QPushButton("Merge CC Content")
        self.merge_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.merge_btn.clicked.connect(self.start_merge)
        
        self.restore_btn = QPushButton("Restore Backup")
        self.restore_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px;")
        self.restore_btn.clicked.connect(self.start_restore)
        
        btn_layout.addWidget(self.merge_btn)
        btn_layout.addWidget(self.restore_btn)
        layout.addLayout(btn_layout)

        # Log
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

    def log(self, message):
        self.log_output.append(message)

    def _disable_buttons(self):
        """Disable merge and restore buttons during operation."""
        self.merge_btn.setEnabled(False)
        self.restore_btn.setEnabled(False)

    def _check_existing_backup(self, fo4_path):
        """Check for existing backups and CC file states.
        
        Returns:
            dict with keys:
                - 'has_ccmerged': bool - If CCMerged files exist
                - 'has_other_cc': bool - If other cc*.ba2 files exist (excluding CCMerged)
                - 'backup_count': int - Number of existing backups
                - 'ccmerged_files': list - Names of CCMerged files found
                - 'other_cc_files': list - Names of other CC files found
        """
        from pathlib import Path
        data_path = Path(fo4_path) / "Data"
        backup_dir = data_path / "CC_Backup"
        
        # Get all cc*.ba2 files
        all_cc_files = list(data_path.glob("cc*.ba2"))
        
        # Separate into CCMerged and other
        ccmerged_files = [f.name for f in all_cc_files if f.name.lower().startswith("ccmerged")]
        other_cc_files = [f.name for f in all_cc_files if not f.name.lower().startswith("ccmerged")]
        
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

    def _show_merge_status(self, fo4_path):
        """Display the current merge/backup status and update button states."""
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

    def _handle_merge_with_mixed_files(self, fo4_path):
        """Handle merge attempt when both CCMerged and other CC files exist.
        
        Returns:
            True if user wants to continue with merge
            False if user cancels
        """
        status = self._check_existing_backup(fo4_path)
        
        if status['has_ccmerged'] and status['has_other_cc']:
            reply = QMessageBox.warning(
                self,
                "Merged Files Already Exist",
                f"Found {len(status['ccmerged_files'])} merged archive(s) and "
                f"{len(status['other_cc_files'])} unmerged CC file(s).\n\n"
                "This will create new merged archives.\n"
                "It is recommended to RESTORE your backup first,\n"
                "then merge all files together.\n\n"
                "Continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            return reply == QMessageBox.StandardButton.Yes
        
        return True

    def _is_admin(self):
        """Check if the application is running with administrator privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False

    def _is_protected_path(self, path):
        """Check if a path is in a Windows-protected location."""
        protected_prefixes = [
            os.environ.get('ProgramFiles', r'C:\Program Files'),
            os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)'),
            os.environ.get('SystemRoot', r'C:\Windows'),
        ]
        path_lower = path.lower()
        return any(path_lower.startswith(p.lower()) for p in protected_prefixes if p)

    def _check_elevation_needed(self, path):
        """Warn user if elevation may be required for the given path."""
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
        # Try to detect FO4
        # Common paths
        common_paths = [
            r"C:\Program Files (x86)\Steam\steamapps\common\Fallout 4",
            r"C:\Program Files\Steam\steamapps\common\Fallout 4",
            r"D:\SteamLibrary\steamapps\common\Fallout 4"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                self.fo4_input.setText(path)
                self.check_archive2(path)
                self._show_merge_status(path)
                self._check_elevation_needed(path)
                break

    def check_archive2(self, fo4_path):
        # Check default location
        default_a2 = os.path.join(fo4_path, "Tools", "Archive2", "Archive2.exe")
        if os.path.exists(default_a2):
            self.a2_input.setText(default_a2)
            self.log("Archive2.exe found automatically.")
        else:
            self.log("Archive2.exe not found in default location.")
            reply = QMessageBox.question(self, "Archive2 Missing", 
                                       "Archive2.exe was not found in the default location.\n\n"
                                       "It is required to pack BA2 files. It comes with the Creation Kit.\n\n"
                                       "Would you like to open the Steam page for the Creation Kit?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                webbrowser.open("steam://install/1946160")

    def browse_fo4(self):
        path = QFileDialog.getExistingDirectory(self, "Select Fallout 4 Directory")
        if path:
            self.fo4_input.setText(path)
            self.check_archive2(path)
            self._show_merge_status(path)
            self._check_elevation_needed(path)

    def browse_archive2(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Archive2.exe", filter="Executables (*.exe)")
        if path:
            self.a2_input.setText(path)

    def start_merge(self):
        fo4 = self.fo4_input.text()
        a2 = self.a2_input.text()

        if not fo4 or not os.path.exists(fo4):
            QMessageBox.warning(self, "Error", "Invalid Fallout 4 path.")
            return
        if not a2 or not os.path.exists(a2):
            QMessageBox.warning(self, "Error", "Invalid Archive2 path.")
            return

        # Check current state and handle appropriately
        status = self._check_existing_backup(fo4)
        
        # Case 1: Only merged files exist - can't merge
        if status['has_ccmerged'] and not status['has_other_cc']:
            QMessageBox.information(
                self,
                "All Files Merged",
                "All Creation Club files are already merged.\n\n"
                "To merge additional CC files:\n"
                "1. Click 'Restore Backup'\n"
                "2. Add new CC files to Data folder\n"
                "3. Click 'Merge CC Content' again"
            )
            return
        
        # Case 2: Mixed merged and unmerged files - warn user
        if not self._handle_merge_with_mixed_files(fo4):
            self.log("Merge cancelled by user.")
            return

        self._disable_buttons()
        self.log("Starting merge process...")
        
        self.worker = MergeWorker(self.merger, fo4, a2)
        self.worker.progress.connect(self.log)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def start_restore(self):
        fo4 = self.fo4_input.text()
        if not fo4 or not os.path.exists(fo4):
            QMessageBox.warning(self, "Error", "Invalid Fallout 4 path.")
            return

        self._disable_buttons()
        self.log("Starting restore process...")

        self.worker = RestoreWorker(self.merger, fo4)
        self.worker.progress.connect(self.log)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_finished(self, success, message):
        self.merge_btn.setEnabled(True)
        self.restore_btn.setEnabled(True)
        if success:
            QMessageBox.information(self, "Success", message)
            self.log(f"DONE: {message}")
        else:
            QMessageBox.critical(self, "Error", message)
            self.log(f"ERROR: {message}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
