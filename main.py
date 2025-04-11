import sys
import os
import json
import random
import re
import time
import traceback
from typing import Any, Dict, List

# Consolidated PyQt5 imports.
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QSizePolicy, QLabel, QListWidget, QListWidgetItem, QMenu,
    QLineEdit, QFileDialog, QMessageBox, QStatusBar, QAction, QFormLayout,
    QCheckBox, QDockWidget, QPlainTextEdit, QTableWidget, QTableWidgetItem,
    QInputDialog, QProgressDialog, QAbstractItemView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFontMetrics, QIcon

import qtmodern.styles
import qtmodern.windows

# Constants for file names.
CONFIG_FILE = "config.json"
MAPPING_FILE = "additive_mappings.json"

# Default values for animation file settings.
DEFAULT_SETTINGS: Dict[str, Any] = {
    "OutputFramerate": 30,
    "EnableLeftHandIK": True,
    "EnableRightHandIK": True,
    "UseExperimentalFeatures": True,
    "LeftIKTargetBoneName": "tag_ik_loc_le",
    "RightIKTargetBoneName": "tag_ik_loc_ri"
}

# Default mapping entries.
DEFAULT_MAPPING: Dict[str, Any] = {
    "walk_offset_additive,walk_to_sprint": ["sprint_in", 1, 1],
    "sprint_offset_additive,sprint_loop": ["sprint_loop", 1, 1],
    "walk_offset_additive,sprint_to_walk": ["sprint_out", 1, 1],
    "walk_offset_additive,walk_to_super_sprint": ["super_sprint_in", 1, 1],
    "super_sprint_offset_additive,super_sprint_loop": ["super_sprint_loop", 1, 1],
    "walk_offset_additive,super_sprint_to_walk": ["super_sprint_out", 1, 1],
    "walk_offset_additive,jog_loop": ["walk_f", 1, 1],
    "mantle_48_on,mantle_48_on_rhand": ["mantle_48_on", 2, 3],
    "mantle_48_over_back,mantle_48_over_back_rhand": ["mantle_48_over", 2, 3],
    "mantle_48_over_l,mantle_48_over_l_rhand": ["mantle_48_over_l", 2, 3],
    "mantle_48_over_r,mantle_48_over_r_rhand": ["mantle_48_over_r", 2, 3],
    "slide_in,slide_in_rhand": ["slide_in", 2, 3],
    "slide_loop,slide_loop_rhand": ["slide_loop", 2, 3],
    "slide_out,slide_out_rhand": ["slide_out", 2, 3],
    "crawl_f": ["crawl_f", 1],
    "crawl_in": ["crawl_in", 1],
    "crawl_l": ["crawl_l", 1],
    "crawl_r": ["crawl_r", 1]
}


###############################################################################
# Configuration Manager (Model)
###############################################################################
class ConfigManager:
    """Handles loading and saving of configuration and mapping files."""
    def __init__(self, config_file: str = CONFIG_FILE, mapping_file: str = MAPPING_FILE) -> None:
        self.config_file = config_file
        self.mapping_file = mapping_file
        self.config: Dict[str, Any] = {}
        self.mappings: Dict[str, Any] = {}
        self.load_all()

    def load_all(self) -> None:
        self.load_config()
        self.load_mappings()

    def load_config(self) -> None:
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    self.config = json.load(f)
            else:
                self.config = {}
        except Exception as e:
            self.config = {}
            print(f"Error loading config: {e}")

    def save_config(self) -> None:
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def load_mappings(self) -> None:
        try:
            if os.path.exists(self.mapping_file):
                with open(self.mapping_file, "r") as f:
                    self.mappings = json.load(f)
            else:
                self.mappings = DEFAULT_MAPPING.copy()
                with open(self.mapping_file, "w") as f:
                    json.dump(self.mappings, f, indent=4)
        except Exception as e:
            self.mappings = {}
            print(f"Error loading mappings: {e}")

    def save_mappings(self) -> None:
        try:
            with open(self.mapping_file, "w") as f:
                json.dump(self.mappings, f, indent=4)
        except Exception as e:
            print(f"Error saving mappings: {e}")


###############################################################################
# Mapping Editor Dialog (View for Mapping Management)
###############################################################################
from PyQt5.QtWidgets import QDialog  # Imported here since this view is separate.

class MappingEditorDialog(QDialog):
    """Dialog for editing animation mapping entries."""
    def __init__(self, config_manager: ConfigManager, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Mapping Editor")
        self.config_manager = config_manager
        self.resize(500, 300)
        layout = QVBoxLayout(self)

        # Table for mappings.
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Key", "Values (comma-separated)"])
        layout.addWidget(self.table)
        self.load_table()

        # Buttons for CRUD operations.
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.edit_button = QPushButton("Edit")
        self.remove_button = QPushButton("Remove")
        self.import_button = QPushButton("Import")
        self.export_button = QPushButton("Export")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.export_button)
        layout.addLayout(button_layout)

        # Connect button signals.
        self.add_button.clicked.connect(self.add_entry)
        self.edit_button.clicked.connect(self.edit_entry)
        self.remove_button.clicked.connect(self.remove_entry)
        self.import_button.clicked.connect(self.import_mappings)
        self.export_button.clicked.connect(self.export_mappings)

        # Set tooltips.
        self.add_button.setToolTip("Add a new mapping entry.")
        self.edit_button.setToolTip("Edit the selected mapping entry.")
        self.remove_button.setToolTip("Remove the selected mapping entry.")
        self.import_button.setToolTip("Import mappings from a JSON file.")
        self.export_button.setToolTip("Export current mappings to a JSON file.")

    def load_table(self) -> None:
        self.table.setRowCount(0)
        for key, value in self.config_manager.mappings.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            key_item = QTableWidgetItem(key)
            value_str = ",".join(str(v) for v in value)
            value_item = QTableWidgetItem(value_str)
            self.table.setItem(row, 0, key_item)
            self.table.setItem(row, 1, value_item)

    def add_entry(self) -> None:
        key, ok = QInputDialog.getText(self, "Add Mapping", "Enter mapping key (comma-separated fragments):")
        if ok and key:
            values, ok_val = QInputDialog.getText(self, "Add Mapping", "Enter mapping values (comma-separated):")
            if ok_val and values:
                value_list: List[Any] = []
                for part in values.split(","):
                    part = part.strip()
                    try:
                        value_list.append(int(part))
                    except ValueError:
                        value_list.append(part)
                self.config_manager.mappings[key] = value_list
                self.config_manager.save_mappings()
                self.load_table()
                if self.parent() is not None and hasattr(self.parent(), 'log_message'):
                    self.parent().log_message(f"Mapping added: {key} -> {value_list}")

    def edit_entry(self) -> None:
        current_item = self.table.currentItem()
        if current_item:
            row = current_item.row()
            key_item = self.table.item(row, 0)
            value_item = self.table.item(row, 1)
            key = key_item.text()
            new_key, ok = QInputDialog.getText(self, "Edit Mapping", "Edit mapping key:", text=key)
            if ok and new_key:
                new_values, ok_val = QInputDialog.getText(self, "Edit Mapping", "Edit mapping values (comma-separated):", text=value_item.text())
                if ok_val and new_values:
                    value_list = []
                    for part in new_values.split(","):
                        part = part.strip()
                        try:
                            value_list.append(int(part))
                        except ValueError:
                            value_list.append(part)
                    if new_key != key:
                        del self.config_manager.mappings[key]
                    self.config_manager.mappings[new_key] = value_list
                    self.config_manager.save_mappings()
                    self.load_table()
                    if self.parent() is not None and hasattr(self.parent(), 'log_message'):
                        self.parent().log_message(f"Mapping edited: {new_key} -> {value_list}")

    def remove_entry(self) -> None:
        current_item = self.table.currentItem()
        if current_item:
            row = current_item.row()
            key_item = self.table.item(row, 0)
            key = key_item.text()
            del self.config_manager.mappings[key]
            self.config_manager.save_mappings()
            self.load_table()
            if self.parent() is not None and hasattr(self.parent(), 'log_message'):
                self.parent().log_message(f"Mapping removed: {key}")

    def import_mappings(self) -> None:
        fname, _ = QFileDialog.getOpenFileName(self, "Import Mappings", "", "JSON Files (*.json)")
        if fname:
            try:
                with open(fname, "r") as f:
                    imported = json.load(f)
                self.config_manager.mappings.update(imported)
                self.config_manager.save_mappings()
                self.load_table()
                if self.parent() is not None and hasattr(self.parent(), 'log_message'):
                    self.parent().log_message(f"Imported mappings from: {fname}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import mappings: {e}")

    def export_mappings(self) -> None:
        fname, _ = QFileDialog.getSaveFileName(self, "Export Mappings", "", "JSON Files (*.json)")
        if fname:
            try:
                with open(fname, "w") as f:
                    json.dump(self.config_manager.mappings, f, indent=4)
                if self.parent() is not None and hasattr(self.parent(), 'log_message'):
                    self.parent().log_message(f"Exported mappings to: {fname}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export mappings: {e}")


###############################################################################
# Drag & Drop Widgets (View)
###############################################################################
class DragDropBox(QFrame):
    """A drop area for single file types (e.g., idle, left pose, skeleton, etc.)."""
    def __init__(self, filetype: str, config_key: str, update_callback, placeholder: str = "") -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px dashed #555;
                border-radius: 6px;
            }
            QLabel {
                color: #888;
                font-size: 10pt;
            }
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumSize(120, 50)
        self.filetype = filetype
        self.config_key = config_key
        self.update_callback = update_callback
        self.placeholder = placeholder

        self.filename_label = QLabel("")
        self.filename_label.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addStretch()
        layout.addWidget(self.filename_label)
        layout.addStretch()
        self.setLayout(layout)
        self.set_placeholder()
        self.setToolTip(f"Drag a .{self.filetype} file here.")

    def set_placeholder(self) -> None:
        self.filename_label.setText(self.placeholder)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        if urls:
            filepath = urls[0].toLocalFile()
            if filepath.endswith(f".{self.filetype}"):
                filename = os.path.basename(filepath)
                self.set_filename_display(filename)
                self.update_callback(self.config_key, filepath)
                if hasattr(self.window(), 'log_message'):
                    self.window().log_message(f"File dropped: {filepath} assigned to {self.config_key}")
            else:
                self.set_filename_display("Invalid file")
                if hasattr(self.window(), 'log_message'):
                    self.window().log_message(f"Invalid file dropped: {filepath} (expected .{self.filetype})")

    def set_filename_display(self, name: str) -> None:
        metrics = QFontMetrics(self.filename_label.font())
        elided = metrics.elidedText(name, Qt.ElideMiddle, self.width() - 20)
        self.filename_label.setText(elided)


class AnimationDropArea(QFrame):
    """A drop area for additive animations with internal reordering support."""
    def __init__(self, update_callback, initial_files: List[str] = None) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1e1e1e dashed #555;
                border-radius: 6px;
            }
            QListWidget {
                background-color: #1e1e1e;
                color: #ccc;
                border: none;
            }
            QListWidget::item:hover {
                background-color: #333333;
            }
            QListWidget::item:selected {
                background-color: #555555;
            }
        """)
        self.setMinimumHeight(120)
        self.update_callback = update_callback
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("padding: 5px;")
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.setToolTip("Drag and drop .seanim files here for additive animations.")
        if initial_files:
            for f in initial_files:
                self.add_file(f)

    def on_item_clicked(self, item: QListWidgetItem) -> None:
        main_app = self.window().findChild(AlchemistAdditiveApp)
        if main_app:
            main_app.on_animation_item_clicked(item.toolTip())

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.endswith(".seanim"):
                self.add_file(path)
                files.append(path)
        if files:
            self.update_callback("animations", self.get_all_files())
            if hasattr(self.window(), 'log_message'):
                self.window().log_message(f"Added additive animations: {files}")

    def add_file(self, path: str) -> None:
        if path not in self.get_all_files():
            item = QListWidgetItem(os.path.basename(path))
            item.setToolTip(path)
            self.list_widget.addItem(item)

    def get_all_files(self) -> List[str]:
        return [self.list_widget.item(i).toolTip() for i in range(self.list_widget.count())]

    def show_context_menu(self, position) -> None:
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
        menu = QMenu()
        remove_action = menu.addAction("Remove Animation From List")
        clear_action = menu.addAction("Clear All")
        action = menu.exec_(self.list_widget.mapToGlobal(position))
        if action == remove_action:
            for item in selected_items:
                row = self.list_widget.row(item)
                self.list_widget.takeItem(row)
            self.update_callback("animations", self.get_all_files())
            if hasattr(self.window(), 'log_message'):
                self.window().log_message("Removed selected additive animations.")
        elif action == clear_action:
            self.list_widget.clear()
            self.update_callback("animations", [])
            if hasattr(self.window(), 'log_message'):
                self.window().log_message("Cleared all additive animations.")


class NormalAnimationDropArea(QFrame):
    """A drop area for normal animations with drag and drop reordering."""
    def __init__(self, update_callback, initial_files: List[str] = None) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1e1e1e dashed #555;
                border-radius: 6px;
            }
            QListWidget {
                background-color: #1e1e1e;
                color: #ccc;
                border: none;
            }
            QListWidget::item:hover {
                background-color: #333333;
            }
            QListWidget::item:selected {
                background-color: #555555;
            }
        """)
        self.setMinimumHeight(120)
        self.update_callback = update_callback
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("padding: 5px;")
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.setToolTip("Drop normal animation files here.")
        if initial_files:
            for f in initial_files:
                self.add_file(f)

    def on_item_clicked(self, item: QListWidgetItem) -> None:
        main_app = self.window().findChild(AlchemistAdditiveApp)
        if main_app:
            main_app.on_animation_item_clicked(item.toolTip())

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            self.add_file(path)
            files.append(path)
        if files:
            self.update_callback("normal_anims", self.get_all_files())
            if hasattr(self.window(), 'log_message'):
                self.window().log_message(f"Added normal animations: {files}")

    def add_file(self, path: str) -> None:
        if path not in self.get_all_files():
            item = QListWidgetItem(os.path.basename(path))
            item.setToolTip(path)
            self.list_widget.addItem(item)

    def get_all_files(self) -> List[str]:
        return [self.list_widget.item(i).toolTip() for i in range(self.list_widget.count())]

    def show_context_menu(self, position) -> None:
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
        menu = QMenu()
        remove_action = menu.addAction("Remove Animation From List")
        clear_action = menu.addAction("Clear All")
        action = menu.exec_(self.list_widget.mapToGlobal(position))
        if action == remove_action:
            for item in selected_items:
                row = self.list_widget.row(item)
                self.list_widget.takeItem(row)
            self.update_callback("normal_anims", self.get_all_files())
            if hasattr(self.window(), 'log_message'):
                self.window().log_message("Removed selected normal animations.")
        elif action == clear_action:
            self.list_widget.clear()
            self.update_callback("normal_anims", [])
            if hasattr(self.window(), 'log_message'):
                self.window().log_message("Cleared all normal animations.")


class OutputPathSelector(QWidget):
    """Widget to select the output folder."""
    def __init__(self, initial_path: str, update_callback) -> None:
        super().__init__()
        self.update_callback = update_callback
        layout = QHBoxLayout()
        self.edit = QLineEdit()
        self.edit.setText(initial_path)
        self.button = QPushButton("Browse")
        self.button.clicked.connect(self.browse)
        layout.addWidget(QLabel("Output Folder:"))
        layout.addWidget(self.edit)
        layout.addWidget(self.button)
        self.setLayout(layout)
        self.edit.textChanged.connect(lambda text: self.on_text_changed(text))
        self.setToolTip("Specify the folder where the animations will be saved.")

    def on_text_changed(self, text: str) -> None:
        self.update_callback("output_path", text)
        if self.parent() is not None and hasattr(self.parent(), 'log_message'):
            self.parent().log_message(f"Output folder changed: {text}")

    def browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if path:
            self.edit.setText(path)
            self.update_callback("output_path", path)
            if self.parent() is not None and hasattr(self.parent(), 'log_message'):
                self.parent().log_message(f"Output folder selected: {path}")


###############################################################################
# Project Creator Worker (Controller)
###############################################################################
class ProjectCreator(QThread):
    """Worker thread to create the project file without freezing the UI."""
    progress_changed = pyqtSignal(int)
    log_message = pyqtSignal(str)
    project_created = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, config: Dict[str, Any], mappings: Dict[str, Any], parent: QWidget = None) -> None:
        super().__init__(parent)
        self.config = config
        self.mappings = mappings

    def run(self) -> None:
        try:
            self.log_message.emit("Starting project file creation...")
            self.progress_changed.emit(10)

            # Retrieve required file paths from configuration.
            idle = self.config.get("idle_anim")
            left = self.config.get("left_pose")
            right = self.config.get("right_pose")
            skel = self.config.get("skeleton")
            anims = self.config.get("animations", [])
            normal_anims = self.config.get("normal_anims", [])
            output_path = self.config.get("output_path")

            # Global IK override values.
            global_left = self.config.get("LeftIKTargetBoneName", "").strip()
            global_right = self.config.get("RightIKTargetBoneName", "").strip()

            if not all([idle, left, right, skel, output_path]):
                self.error_occurred.emit("Missing one or more required files or output path.")
                self.log_message.emit("Error: Missing required files or output path.")
                return

            anim_entries = []
            id_counter = 3
            idle_settings = self.config.get("file_settings", {}).get(idle, DEFAULT_SETTINGS.copy())
            self.log_message.emit(f"Idle settings loaded: {idle_settings}")

            # Process mappings for additive animations.
            for map_key, values in self.mappings.items():
                output_name = values[0]
                types = values[1:]
                fragments = map_key.split(",")
                layer_anims = []
                found_all = True

                for frag in fragments:
                    matched = [a for a in anims if frag in os.path.basename(a)]
                    if matched:
                        layer_anims.append(matched[0])
                    else:
                        found_all = False
                        break

                if not found_all:
                    continue

                base_name = os.path.basename(idle)
                final_name = os.path.splitext(base_name)[0].rsplit("_", 1)[0] + f"_{output_name}"
                entry_id = str(id_counter)
                layer_id = str(id_counter + 1)

                layer_values = []
                for idx, anim_path in enumerate(layer_anims):
                    settings = self.config.get("file_settings", {}).get(anim_path, DEFAULT_SETTINGS.copy())
                    layer_values.append({
                        "$id": str(id_counter + 2 + idx),
                        "Owner": {"$ref": entry_id},
                        "Name": anim_path,
                        "Offset": None,
                        "Color": random.randint(10000000, 99999999),
                        "Type": types[idx] if idx < len(types) else types[-1]
                    })

                anim_entries.append({
                    "$id": entry_id,
                    "OutputFramerate": idle_settings["OutputFramerate"],
                    "Name": idle,
                    "OutputName": final_name,
                    "OutputFolder": output_path,
                    "SkeletonPath": skel,
                    "EnableLeftHandIK": idle_settings["EnableLeftHandIK"],
                    "EnableRightHandIK": idle_settings["EnableRightHandIK"],
                    "UseExperimentalFeatures": idle_settings["UseExperimentalFeatures"],
                    "LeftHandPoseFile": left,
                    "RightHandPoseFile": right,
                    "LeftIKTargetBoneName": global_left if global_left else idle_settings["LeftIKTargetBoneName"],
                    "RightIKTargetBoneName": global_right if global_right else idle_settings["RightIKTargetBoneName"],
                    "Layers": {
                        "$id": layer_id,
                        "$values": layer_values
                    }
                })
                id_counter += 2 + len(layer_anims)
                self.log_message.emit(f"Processed additive mapping: {map_key} -> {final_name}")

            # Process normal animations.
            for norm_anim in normal_anims:
                base_name = os.path.basename(norm_anim)
                output_name = os.path.splitext(base_name)[0]
                settings = self.config.get("file_settings", {}).get(norm_anim, DEFAULT_SETTINGS.copy())
                entry_id = str(id_counter)
                layer_id = str(id_counter + 1)
                layer_entry = {
                    "$id": str(id_counter + 2),
                    "Owner": {"$ref": entry_id},
                    "Name": norm_anim,
                    "Offset": None,
                    "Color": random.randint(10000000, 99999999),
                    "Type": 0
                }
                anim_entry = {
                    "$id": entry_id,
                    "OutputFramerate": settings["OutputFramerate"],
                    "Name": idle,
                    "OutputName": output_name,
                    "OutputFolder": output_path,
                    "SkeletonPath": skel,
                    "EnableLeftHandIK": settings["EnableLeftHandIK"],
                    "EnableRightHandIK": settings["EnableRightHandIK"],
                    "UseExperimentalFeatures": settings["UseExperimentalFeatures"],
                    "LeftHandPoseFile": left,
                    "RightHandPoseFile": right,
                    "LeftIKTargetBoneName": global_left if global_left else settings["LeftIKTargetBoneName"],
                    "RightIKTargetBoneName": global_right if global_right else settings["RightIKTargetBoneName"],
                    "Layers": {
                        "$id": layer_id,
                        "$values": [layer_entry]
                    }
                }
                anim_entries.append(anim_entry)
                id_counter += 3
                self.log_message.emit(f"Processed normal animation: {norm_anim}")

            if not anim_entries:
                anim_entries.append({
                    "$id": str(id_counter),
                    "OutputFramerate": idle_settings["OutputFramerate"],
                    "Name": idle,
                    "OutputName": os.path.splitext(os.path.basename(idle))[0],
                    "OutputFolder": output_path,
                    "SkeletonPath": skel,
                    "EnableLeftHandIK": idle_settings["EnableLeftHandIK"],
                    "EnableRightHandIK": idle_settings["EnableRightHandIK"],
                    "UseExperimentalFeatures": idle_settings["UseExperimentalFeatures"],
                    "LeftHandPoseFile": left,
                    "RightHandPoseFile": right,
                    "LeftIKTargetBoneName": global_left if global_left else idle_settings["LeftIKTargetBoneName"],
                    "RightIKTargetBoneName": global_right if global_right else idle_settings["RightIKTargetBoneName"],
                    "Layers": {
                        "$id": str(id_counter + 1),
                        "$values": []
                    }
                })
                self.log_message.emit("No animation entries processed; using idle animation only.")

            self.progress_changed.emit(60)
            project = {
                "$id": "1",
                "EnableAnimationTrimming": False,
                "LeftIKStartBoneName": "j_shoulder_le",
                "LeftIKMidBoneName": "j_elbow_le",
                "LeftIKEndBoneName": "j_wrist_le",
                "LeftIKTargetBoneName": idle_settings["LeftIKTargetBoneName"],
                "RightIKStartBoneName": "j_shoulder_ri",
                "RightIKMidBoneName": "j_elbow_ri",
                "RightIKEndBoneName": "j_wrist_ri",
                "RightIKTargetBoneName": idle_settings["RightIKTargetBoneName"],
                "OutputPrefix": "",
                "OutputSuffix": "",
                "OutputFormat": ".seanim",
                "Animations": {
                    "$id": "2",
                    "$values": anim_entries
                }
            }

            project_folder = os.path.join(os.path.dirname(__file__), "Projects")
            os.makedirs(project_folder, exist_ok=True)
            out_name = os.path.splitext(os.path.basename(idle))[0]
            out_path = os.path.join(project_folder, f"{out_name}.aprj")
            with open(out_path, "w") as f:
                json.dump(project, f, indent=4)

            self.progress_changed.emit(100)
            self.log_message.emit(f"Project file saved: {out_path}")
            self.project_created.emit(out_path)
        except Exception as e:
            err_msg = f"Error creating project: {e}\n{traceback.format_exc()}"
            self.error_occurred.emit(err_msg)
            self.log_message.emit(err_msg)


###############################################################################
# Main Application Window (View + Controller)
###############################################################################
class DefaultWidthButton(QPushButton):
    def sizeHint(self):
        hint = super().sizeHint()
        # Return a QSize with 800 as the preferred width.
        return hint.expandedTo(QSize(800, hint.height()))


class AlchemistAdditiveApp(QMainWindow):
    """Main window for the Additive Animation Creator application."""
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Alchemist Project Creator")
        self.setWindowIcon(QIcon("icon.ico"))
        self.resize(800, 600)
        self.config_manager = ConfigManager()
        self.selected_anim_file: str = ""
        self.setStatusBar(QStatusBar())
        self.init_menu()
        self.init_ui()
        self.populate_fields()

    def init_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        exit_action.setToolTip("Exit the application.")
        file_menu.addAction(exit_action)

        edit_menu = menubar.addMenu("Edit")
        reset_action = QAction("Reset Configuration", self)
        reset_action.triggered.connect(self.reset_configuration)
        reset_action.setToolTip("Reset configuration to default settings.")
        edit_menu.addAction(reset_action)

        mapping_editor_action = QAction("Mapping Editor", self)
        mapping_editor_action.triggered.connect(self.open_mapping_editor)
        mapping_editor_action.setToolTip("Edit the mapping file in a dedicated window.")
        edit_menu.addAction(mapping_editor_action)

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        about_action.setToolTip("Show application information.")
        help_menu.addAction(about_action)

    def init_ui(self) -> None:
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Output path selector.
        self.output_selector = OutputPathSelector(self.config_manager.config.get("output_path", ""), self.update_config)
        main_layout.addWidget(self.output_selector)

        # ---------------------------------------------------------------------------
        # Added Global IK Override text boxes (placed below output path selector)
        ik_override_layout = QHBoxLayout()

        left_ik_layout = QVBoxLayout()
        left_ik_label = QLabel("Left IK Global Override")
        self.left_ik_text = QLineEdit()
        self.left_ik_text.setToolTip("Enter a global override for Left IK Target Bone Name.")
        self.left_ik_text.textChanged.connect(lambda text: self.update_config("LeftIKTargetBoneName", text))
        left_ik_layout.addWidget(left_ik_label)
        left_ik_layout.addWidget(self.left_ik_text)

        right_ik_layout = QVBoxLayout()
        right_ik_label = QLabel("Right IK Global Override")
        self.right_ik_text = QLineEdit()
        self.right_ik_text.setToolTip("Enter a global override for Right IK Target Bone Name.")
        self.right_ik_text.textChanged.connect(lambda text: self.update_config("RightIKTargetBoneName", text))
        right_ik_layout.addWidget(right_ik_label)
        right_ik_layout.addWidget(self.right_ik_text)

        ik_override_layout.addLayout(left_ik_layout)
        ik_override_layout.addLayout(right_ik_layout)
        main_layout.addLayout(ik_override_layout)
        # ---------------------------------------------------------------------------

        # Upper row for idle, skeleton, and pose files.
        h_layout = QHBoxLayout()
        self.idle_box = DragDropBox("seanim", "idle_anim", self.update_config, "Drag Idle Animation \n(.seanim)")
        self.left_box = DragDropBox("seanim", "left_pose", self.update_config, "Drag Left Pose File \n(.seanim)")
        self.right_box = DragDropBox("seanim", "right_pose", self.update_config, "Drag Right Pose File \n(.seanim)")
        self.skel_box = DragDropBox("semodel", "skeleton", self.update_config, "Drag Skeleton File \n(.semodel)")
        for box in [self.idle_box, self.skel_box, self.left_box, self.right_box]:
            h_layout.addWidget(box)
        main_layout.addLayout(h_layout)

        # Side-by-side layout for animation drop areas.
        anims_hlayout = QHBoxLayout()
        additive_vlayout = QVBoxLayout()
        additive_label = QLabel("Additive Animations")
        additive_label.setStyleSheet("color: #aaa; font-size: 10pt;")
        initial_anims = self.config_manager.config.get("animations", [])
        self.anim_drop_area = AnimationDropArea(self.update_config, initial_anims)
        additive_vlayout.addWidget(additive_label)
        additive_vlayout.addWidget(self.anim_drop_area)
        normal_vlayout = QVBoxLayout()
        normal_label = QLabel("Normal Animations")
        normal_label.setStyleSheet("color: #aaa; font-size: 10pt;")
        initial_normal_anims = self.config_manager.config.get("normal_anims", [])
        self.normal_anim_drop_area = NormalAnimationDropArea(self.update_config, initial_normal_anims)
        normal_vlayout.addWidget(normal_label)
        normal_vlayout.addWidget(self.normal_anim_drop_area)
        anims_hlayout.addLayout(additive_vlayout)
        anims_hlayout.addLayout(normal_vlayout)
        main_layout.addLayout(anims_hlayout)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Button to create project file.
        self.create_button = DefaultWidthButton("Create Project File")
        self.create_button.clicked.connect(self.create_project_file)
        self.create_button.setStyleSheet("padding: 5px; font-weight: bold;")
        self.create_button.setToolTip("Click to generate the project file based on current configuration.")
        self.create_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.create_button, alignment=Qt.AlignCenter)

        # Integrated logging dock.
        self.init_logging_dock()

    def init_logging_dock(self) -> None:
        self.log_dock = QDockWidget("Log", self)
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_dock.setWidget(self.log_text)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock)

    def log_message(self, message: str) -> None:
        """Append a log message to the integrated logging window."""
        self.log_text.appendPlainText(message)
        self.statusBar().showMessage(message, 5000)

    def open_mapping_editor(self) -> None:
        dialog = MappingEditorDialog(self.config_manager, self)
        dialog.exec_()
        self.log_message("Opened mapping editor.")

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            "About",
            "BO3 Additive Animation Creator\nVersion 1.0\nCreated with PyQt5 and qtmodern.\n\n"
            "All credit goes to Scobalula for creating Alchemist.\n\n"
            "This version includes enhanced UI, logging, mapping editing, and multi-threaded processing."
        )
        self.log_message("Displayed About information.")

    def update_config(self, key: str, value: Any) -> None:
        """Update configuration, save it, and log the change."""
        self.config_manager.config[key] = value
        self.config_manager.save_config()
        self.log_message(f"Configuration updated: {key} -> {value}")

    def populate_fields(self) -> None:
        for box in [self.idle_box, self.skel_box, self.left_box, self.right_box]:
            saved_path = self.config_manager.config.get(box.config_key)
            if saved_path and os.path.exists(saved_path):
                box.set_filename_display(os.path.basename(saved_path))
                self.log_message(f"Populated field {box.config_key}: {saved_path}")
        # Set the global IK override fields if already defined.
        left_override = self.config_manager.config.get("LeftIKTargetBoneName", "")
        right_override = self.config_manager.config.get("RightIKTargetBoneName", "")
        self.left_ik_text.setText(left_override)
        self.right_ik_text.setText(right_override)

    def on_animation_item_clicked(self, file_path: str) -> None:
        self.selected_anim_file = file_path
        file_settings = self.config_manager.config.get("file_settings", {}).get(file_path, DEFAULT_SETTINGS.copy())
        self.log_message(f"Selected animation: {file_path}")

    def reset_configuration(self) -> None:
        reply = QMessageBox.question(
            self,
            "Reset Configuration",
            "Are you sure you want to reset the configuration? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if os.path.exists(CONFIG_FILE):
                try:
                    os.remove(CONFIG_FILE)
                    self.log_message("Configuration file removed.")
                except Exception as e:
                    self.log_message(f"Error resetting configuration: {e}")
            self.config_manager.config = {"file_settings": {}}
            self.output_selector.edit.clear()
            for box in [self.idle_box, self.skel_box, self.left_box, self.right_box]:
                box.set_placeholder()
            self.anim_drop_area.list_widget.clear()
            self.normal_anim_drop_area.list_widget.clear()
            self.log_message("Configuration reset.")

    def create_project_file(self) -> None:
        self.prog_dialog = QProgressDialog("Please wait while the project file is being created...", "Cancel", 0, 100, self)
        self.prog_dialog.setWindowTitle("Creating Project")
        self.prog_dialog.setWindowModality(Qt.WindowModal)
        self.prog_dialog.setValue(10)
        self.prog_dialog.show()

        # Create and start the worker thread.
        self.worker = ProjectCreator(self.config_manager.config, self.config_manager.mappings)
        self.worker.log_message.connect(self.log_message)
        self.worker.project_created.connect(self.on_project_created)
        self.worker.error_occurred.connect(self.on_project_error)
        self.worker.start()

        def update_progress(v: int) -> None:
            self.prog_dialog.setValue(v)
            self.prog_dialog.setLabelText(f"Progress: {v}%")

        self.worker.progress_changed.connect(update_progress)
        self.log_message("Project creation initiated.")

    def on_project_created(self, out_path: str) -> None:
        self.prog_dialog.close()
        QMessageBox.information(self, "Project Created", f"Project file saved:\n{out_path}")
        self.log_message(f"Project file saved: {out_path}")

    def on_project_error(self, error: str) -> None:
        self.prog_dialog.close()
        QMessageBox.critical(self, "Error Creating Project", error)
        self.log_message(error)


def main() -> None:
    app = QApplication(sys.argv)
    qtmodern.styles.dark(app)
    window = AlchemistAdditiveApp()
    modern_window = qtmodern.windows.ModernWindow(window)
    modern_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
