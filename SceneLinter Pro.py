#
#   SceneLinter Pro
#   A tool for 3ds Max to create, manage, and run a
#   pre-render checklist.
#
#   Author: Iman Shirani
#   Version: 0.0.1 - Added rule management features.
#


import json
import os
import time
from PySide6 import QtWidgets, QtCore, QtGui
from pymxs import runtime as rt

# --- PLACEHOLDERS: PLEASE FILL IN YOUR INFORMATION HERE ---
AUTHOR_NAME = "Iman Shirani"
GITHUB_LINK = "https://github.com/imanshirani/SceneLinter-Pro"
PAYPAL_LINK = "https://www.paypal.com/donate/?hosted_button_id=LAMNRY6DDWDC4"

# --- REFERENCE LINKS ---
LINKS = {
    "3ds Max Developer Help Center": "https://help.autodesk.com/view/MAXDEV/2026/ENU/",
    "MAXScript Help": "https://help.autodesk.com/view/MAXDEV/2026/ENU/?guid=GUID-F039181A-C072-4469-A329-AE60FF7535E7",
    "Python API Reference": "https://help.autodesk.com/view/MAXDEV/2026/ENU/?guid=MAXDEV_Python_about_the_3ds_max_python_api_html",
    "MAXScript Language Reference": "https://help.autodesk.com/view/MAXDEV/2026/ENU/?guid=GUID-6FC81BE7-58FF-4C63-8362-0BDCFA9F904C",
    
}

PRESET_PROPERTIES = {
    "Render Width": "renderWidth", "Render Height": "renderHeight", "Number of Lights": "lights.count",
    "Total Scene Polygons": "polycount.total", "Render Output Path": "rendOutputFilename"
}
# Constants for tree item types
FOLDER_ITEM_TYPE = 1001
RULE_ITEM_TYPE = 1002

# --- HELPER FUNCTION ---
def get_max_main_window():
    try: from shiboken6 import wrapInstance; return wrapInstance(int(rt.windows.getMAXHWND()), QtWidgets.QWidget)
    except: return None

# --- UI DIALOGS (AboutDialog and RuleEditorDialog) ---
class AboutDialog(QtWidgets.QDialog):
    # ... (This class is complete and correct)
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("About SceneLinter Pro"); self.setFixedSize(350, 200)
        layout = QtWidgets.QVBoxLayout(self); layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        title_label = QtWidgets.QLabel("SceneLinter Pro 0.0.1"); title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        author_label = QtWidgets.QLabel(f"Author: {AUTHOR_NAME}")
        github_label = QtWidgets.QLabel(f'<a href="{GITHUB_LINK}">GitHub Repository</a>'); github_label.setOpenExternalLinks(True)
        paypal_label = QtWidgets.QLabel(f'<a href="{PAYPAL_LINK}">Support the Project (PayPal)</a>'); paypal_label.setOpenExternalLinks(True)
        ok_button = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok); ok_button.accepted.connect(self.accept)
        layout.addWidget(title_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter); layout.addStretch(); layout.addWidget(author_label); layout.addWidget(github_label); layout.addWidget(paypal_label); layout.addStretch(); layout.addWidget(ok_button, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
class RuleEditorDialog(QtWidgets.QDialog):
    # ... (This class is complete and correct)
    def __init__(self, parent=None, rule_data=None):
        super().__init__(parent); self.setWindowTitle("Rule Editor"); self.setMinimumWidth(450); self.rule_data = {}
        self.main_layout = QtWidgets.QVBoxLayout(self); self.form_layout = QtWidgets.QFormLayout(); self.name_edit = QtWidgets.QLineEdit(); self.error_msg_edit = QtWidgets.QLineEdit(); self.value_edit = QtWidgets.QLineEdit(); self.fix_script_edit = QtWidgets.QLineEdit()
        self.type_combo = QtWidgets.QComboBox(); self.type_combo.addItems(["property_not_empty", "min_value", "max_value", "property_equals", "collection_property_all_match"])
        prop_layout = QtWidgets.QHBoxLayout(); self.prop_combo = QtWidgets.QComboBox(); self.prop_combo.setEditable(True)
        self.prop_combo.addItems([""] + sorted(PRESET_PROPERTIES.keys())); self.search_btn = QtWidgets.QPushButton("Search...")
        prop_layout.addWidget(self.prop_combo); prop_layout.addWidget(self.search_btn)
        self.form_layout.addRow("Rule Name:", self.name_edit); self.form_layout.addRow("Condition Type:", self.type_combo); self.form_layout.addRow("MaxScript Target/Prop:", prop_layout); self.form_layout.addRow("Expected Value:", self.value_edit); self.form_layout.addRow("Error Message:", self.error_msg_edit); self.form_layout.addRow("Auto-Fix Script:", self.fix_script_edit)
        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel); self.button_box.accepted.connect(self._on_accept); self.button_box.rejected.connect(self.reject)
        self.search_btn.clicked.connect(self._search_properties); self.main_layout.addLayout(self.form_layout); self.main_layout.addWidget(self.button_box)
        if rule_data: self._populate_fields(rule_data)
    def _search_properties(self):
        search_term = self.prop_combo.currentText().lower()
        if not search_term: QtWidgets.QMessageBox.information(self, "Search", "Please type a search term."); return
        found_props = []; search_targets = [("Render Settings", rt.renderers.current, "renderers.current.{}"), ("Viewport", rt.viewport, "viewport.{}"), ("Global Lights", rt.lights, "lights.{}"), ("Global Geometry", rt.geometry, "geometry.{}")]
        if rt.selection.count > 0: selected_obj = rt.selection[0]; search_targets.insert(0, (f"[Selection] {selected_obj.name}", selected_obj, "$.{}"))
        for friendly_name, target_obj, prop_format in search_targets:
            try:
                all_props = dir(target_obj)
                for prop in all_props:
                    if search_term in prop.lower() and not prop.startswith('__'): display_text = f"{friendly_name} -> .{prop}"; final_string = prop_format.format(prop); found_props.append((display_text, final_string))
            except Exception: continue
        if not found_props: QtWidgets.QMessageBox.information(self, "Search Results", f"No properties found containing '{search_term}'."); return
        dialog = QtWidgets.QDialog(self); dialog.setWindowTitle("Search Results"); dialog.setMinimumWidth(350); layout = QtWidgets.QVBoxLayout(dialog); list_widget = QtWidgets.QListWidget()
        for display_text, final_string in sorted(found_props):
            item = QtWidgets.QListWidgetItem(display_text); item.setData(QtCore.Qt.UserRole, final_string); list_widget.addItem(item)
        layout.addWidget(list_widget); list_widget.itemDoubleClicked.connect(dialog.accept)
        if dialog.exec() == QtWidgets.QDialog.Accepted and list_widget.currentItem():
            selected_item = list_widget.currentItem(); full_prop_string = selected_item.data(QtCore.Qt.UserRole); self.prop_combo.setCurrentText(full_prop_string)
    def _populate_fields(self, data):
        self.name_edit.setText(data.get("name", "")); self.error_msg_edit.setText(data.get("error_message", "")); self.fix_script_edit.setText(data.get("fix_script", "")); condition = data.get("condition", {})
        prop_value = condition.get("maxscript_property", ""); friendly_name = prop_value
        for name, command in PRESET_PROPERTIES.items():
            if command == prop_value: friendly_name = name; break
        self.prop_combo.setCurrentText(friendly_name); self.value_edit.setText(str(condition.get("value", ""))); index = self.type_combo.findText(condition.get("type", "")); self.type_combo.setCurrentIndex(index if index != -1 else 0)
    def _on_accept(self):
        prop_text = self.prop_combo.currentText(); maxscript_command = PRESET_PROPERTIES.get(prop_text, prop_text)
        self.rule_data = { "name": self.name_edit.text(), "enabled": True, "condition": { "type": self.type_combo.currentText(), "maxscript_property": maxscript_command, "value": self.value_edit.text() }, "error_message": self.error_msg_edit.text(), "fix_script": self.fix_script_edit.text() }
        self.accept()
    def get_data(self): return self.rule_data


class SceneLinterProUI(QtWidgets.QWidget):
    def __init__(self, parent=None):
        # ... (init logic is the same)
        super().__init__(parent); self.current_file_path = None; self.is_dirty = False; self.init_ui(); self.connect_signals()
        self.error_dialog = QtWidgets.QMessageBox(self); self.error_dialog.setWindowModality(QtCore.Qt.NonModal)
        self.error_dialog.setWindowTitle("Check Failed"); self.error_dialog.setIcon(QtWidgets.QMessageBox.Warning)
        QtCore.QTimer.singleShot(0, self.load_rules_startup)

    def init_ui(self):
        # ... (init_ui is the same)
        main_layout = QtWidgets.QVBoxLayout(self); self.rules_tree = QtWidgets.QTreeWidget(); self.rules_tree.setColumnCount(3)
        self.rules_tree.setHeaderLabels(["Enabled", "Rule / Folder Name", "Condition Type"]); self.rules_tree.setColumnWidth(0, 60)
        self.rules_tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch); self.rules_tree.setAlternatingRowColors(True)
        self.rules_tree.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove); self.rules_tree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.rules_tree.setStyleSheet("QTreeView::item { min-height: 24px; }")
        buttons_layout = QtWidgets.QHBoxLayout(); self.add_rule_btn = QtWidgets.QPushButton("Add Rule"); self.add_folder_btn = QtWidgets.QPushButton("Add Folder")
        self.edit_btn = QtWidgets.QPushButton("Edit"); self.delete_btn = QtWidgets.QPushButton("Delete")
        buttons_layout.addWidget(self.add_rule_btn); buttons_layout.addWidget(self.add_folder_btn); buttons_layout.addWidget(self.edit_btn); buttons_layout.addWidget(self.delete_btn); buttons_layout.addStretch()
        file_actions_layout = QtWidgets.QHBoxLayout(); self.load_btn = QtWidgets.QPushButton("Load Rules..."); self.save_btn = QtWidgets.QPushButton("Save Rules As...")
        file_actions_layout.addStretch(); file_actions_layout.addWidget(self.load_btn); file_actions_layout.addWidget(self.save_btn)
        main_actions_layout = QtWidgets.QHBoxLayout(); self.run_check_btn = QtWidgets.QPushButton("Run Checks & Render")
        self.run_check_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px; border-radius: 3px;")
        main_actions_layout.addStretch(); main_actions_layout.addWidget(self.run_check_btn)
        main_layout.addWidget(QtWidgets.QLabel("<h3>Linter Rules</h3>")); main_layout.addLayout(buttons_layout); main_layout.addWidget(self.rules_tree); main_layout.addLayout(file_actions_layout); main_layout.addLayout(main_actions_layout)

    def connect_signals(self):
        # ... (other connections are the same)
        self.add_rule_btn.clicked.connect(self.add_new_rule); self.add_folder_btn.clicked.connect(self.add_new_folder)
        self.edit_btn.clicked.connect(self.edit_selected_item)
        self.delete_btn.clicked.connect(self.delete_selected_item)
        self.load_btn.clicked.connect(self.load_rules_from); self.save_btn.clicked.connect(self.save_rules_as)
        self.run_check_btn.clicked.connect(self.run_checks)
        self.rules_tree.itemDoubleClicked.connect(self.edit_selected_item)

        # --- MODIFIED: Connect to a dedicated handler function ---
        self.rules_tree.itemChanged.connect(self._handle_item_changed)

    # --- NEW: Handler for checkbox changes and cascading logic ---
    def _handle_item_changed(self, item, column):
        """Handles changes to items, specifically for cascading checkboxes."""
        # Only act on changes in the 'Enabled' column
        if column == 0:
            # Block signals to prevent infinite loops while we change children
            self.rules_tree.blockSignals(True)
            try:
                # If the changed item is a folder, cascade the change to its children
                if item.type() == FOLDER_ITEM_TYPE:
                    new_state = item.checkState(0)
                    self._set_children_check_state(item, new_state)
            finally:
                # Always unblock signals
                self.rules_tree.blockSignals(False)
            
            # Mark the file as dirty since a change was made
            self.set_dirty(True)

    def _set_children_check_state(self, parent_item, state):
        """Recursively sets the check state for all children of a given item."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            child.setCheckState(0, state)
            # If the child is also a folder, continue the cascade
            if child.type() == FOLDER_ITEM_TYPE:
                self._set_children_check_state(child, state)
    
    # --- ALL OTHER METHODS in this class remain the same ---
    def set_dirty(self, dirty_state=True): self.is_dirty = dirty_state
    def add_new_rule(self):
        dialog = RuleEditorDialog(self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            rule_data = dialog.get_data(); rule_data["type"] = "rule"; self._create_tree_item(rule_data); self.set_dirty()
    def add_new_folder(self):
        folder_name, ok = QtWidgets.QInputDialog.getText(self, "Create Folder", "Enter folder name:")
        if ok and folder_name:
            folder_data = {"type": "folder", "name": folder_name, "enabled": True, "children": []}; self._create_tree_item(folder_data); self.set_dirty()
    def _create_tree_item(self, item_data, parent_item=None):
        if parent_item is None:
            selected_item = self.rules_tree.currentItem()
            if selected_item and selected_item.type() == FOLDER_ITEM_TYPE: parent_item = selected_item
            else: parent_item = self.rules_tree.invisibleRootItem()
        tree_item = QtWidgets.QTreeWidgetItem(parent_item, type=RULE_ITEM_TYPE if item_data["type"] == "rule" else FOLDER_ITEM_TYPE)
        self._update_tree_item(tree_item, item_data); return tree_item
    def edit_selected_item(self, item=None, column=None):
        selected_item = item or self.rules_tree.currentItem()
        if not selected_item: return
        if column is not None and column != 1: return
        item_data = selected_item.data(1, QtCore.Qt.UserRole)
        if selected_item.type() == FOLDER_ITEM_TYPE:
            new_name, ok = QtWidgets.QInputDialog.getText(self, "Edit Folder Name", "Enter new name:", text=item_data.get("name", ""))
            if ok and new_name: item_data["name"] = new_name; self._update_tree_item(selected_item, item_data); self.set_dirty()
        elif selected_item.type() == RULE_ITEM_TYPE:
            dialog = RuleEditorDialog(self, rule_data=item_data)
            if dialog.exec() == QtWidgets.QDialog.Accepted:
                updated_data = dialog.get_data(); updated_data["type"] = "rule"; self._update_tree_item(selected_item, updated_data); self.set_dirty()
    def delete_selected_item(self):
        selected_items = self.rules_tree.selectedItems()
        if not selected_items: return
        for item in selected_items: (item.parent() or self.rules_tree.invisibleRootItem()).removeChild(item)
        self.set_dirty()
    def save_rules_as(self):
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Rules File", "", "JSON Files (*.json)");
        if not file_path: return False
        data_to_save = self._tree_to_dict(self.rules_tree.invisibleRootItem())
        try:
            with open(file_path, 'w', encoding='utf-8') as f: json.dump(data_to_save, f, indent=4)
            print(f"SceneLinter: Saved rules to {file_path}"); self.set_dirty(False)
            if self.parentWidget(): self.parentWidget().setWindowTitle(f"SceneLinter Pro - {os.path.basename(file_path)}")
            return True
        except Exception as e: print(f"SceneLinter: Error saving file: {e}"); return False
    def _tree_to_dict(self, parent_item):
        data = []
        for i in range(parent_item.childCount()):
            child_item = parent_item.child(i); item_data = child_item.data(1, QtCore.Qt.UserRole)
            item_data["enabled"] = (child_item.checkState(0) == QtCore.Qt.CheckState.Checked)
            if child_item.type() == FOLDER_ITEM_TYPE: item_data["children"] = self._tree_to_dict(child_item)
            data.append(item_data)
        return data
    def load_rules_from(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load Rules File", "", "JSON Files (*.json)");
        if not file_path: return
        self._read_rules_from_file(file_path)
    def _read_rules_from_file(self, file_path):
        self.current_file_path = file_path
        try:
            with open(file_path, 'r', encoding='utf-8') as f: data = json.load(f)
            self.rules_tree.clear(); self._populate_tree(data, self.rules_tree.invisibleRootItem())
            print(f"SceneLinter: Loaded rules from {file_path}"); self.set_dirty(False)
            if self.parentWidget(): self.parentWidget().setWindowTitle(f"SceneLinter Pro - {os.path.basename(file_path)}")
        except Exception as e: print(f"SceneLinter: Error loading file: {e}")
    def _populate_tree(self, items_data, parent_qt_item):
        for item_data in items_data:
            item_type = FOLDER_ITEM_TYPE if item_data.get("type") == "folder" else RULE_ITEM_TYPE
            tree_item = QtWidgets.QTreeWidgetItem(parent_qt_item, type=item_type)
            self._update_tree_item(tree_item, item_data)
            if item_type == FOLDER_ITEM_TYPE:
                children = item_data.get("children", []); self._populate_tree(children, tree_item); tree_item.setExpanded(True)
    def _update_tree_item(self, item, data):
        item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable); is_enabled = data.get("enabled", True)
        item.setCheckState(0, QtCore.Qt.CheckState.Checked if is_enabled else QtCore.Qt.CheckState.Unchecked)
        item.setText(1, data.get("name", "Unnamed")); item.setData(1, QtCore.Qt.UserRole, data)
        if item.type() == FOLDER_ITEM_TYPE:
            item.setFont(1, QtGui.QFont("Segoe UI", 9, QtGui.QFont.Weight.Bold)); item.setText(2, "Folder")
        else: item.setText(2, data.get("condition", {}).get("type", "N/A"))
    def run_checks(self):
        print("SceneLinter: Starting checks..."); failed_rules_info = []
        self._traverse_tree_for_checks(self.rules_tree.invisibleRootItem(), failed_rules_info)
        if not failed_rules_info: QtWidgets.QMessageBox.information(self, "Success", "All checks passed!")
        else:
            error_messages = [f"- {info['message']}" for info in failed_rules_info]; error_string = "The following scene checks failed:\n\n" + "\n".join(error_messages)
            msg_box = QtWidgets.QMessageBox(self); msg_box.setWindowTitle("Check Failed"); msg_box.setText(error_string); msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            ok_button = msg_box.addButton("OK", QtWidgets.QMessageBox.ButtonRole.AcceptRole); fix_button = msg_box.addButton("Attempt to Fix All", QtWidgets.QMessageBox.ButtonRole.ActionRole)
            msg_box.exec();
            if msg_box.clickedButton() == fix_button: self._run_fixes(failed_rules_info)
    def _traverse_tree_for_checks(self, parent_item, failed_list):
        for i in range(parent_item.childCount()):
            child_item = parent_item.child(i)
            if child_item.checkState(0) == QtCore.Qt.CheckState.Checked:
                if child_item.type() == RULE_ITEM_TYPE:
                    rule_data = child_item.data(1, QtCore.Qt.UserRole); is_valid, msg = self._evaluate_rule(rule_data)
                    if not is_valid: failed_list.append({"message": msg, "fix_script": rule_data.get("fix_script", "")})
                elif child_item.type() == FOLDER_ITEM_TYPE: self._traverse_tree_for_checks(child_item, failed_list)
    def get_default_rules_path(self, tool_name="SceneLinterPro"):
        try:
            user_scripts_path = rt.pathConfig.GetDir(rt.name("userScripts")); settings_folder = os.path.join(user_scripts_path, tool_name)
            os.makedirs(settings_folder, exist_ok=True); return os.path.join(settings_folder, "rules.json")
        except: return None
    def load_rules_startup(self):
        default_path = self.get_default_rules_path();
        if default_path and os.path.exists(default_path): self._read_rules_from_file(default_path); self.set_dirty(False)
    def _run_fixes(self, failed_rules_info):
        print("SceneLinter: Attempting to run fixes...");
        for info in failed_rules_info:
            fix_script = info.get("fix_script")
            if fix_script:
                try: rt.execute(fix_script); print(f"  > Executed fix: {fix_script}")
                except Exception as e: print(f"  > FAILED to execute fix: {fix_script}. Error: {e}")
        QtWidgets.QMessageBox.information(self, "Fix Attempted", "Fixes have been applied. Please run checks again to verify.")
    def _evaluate_rule(self, rule_data):
        condition = rule_data.get("condition", {}); cond_type = condition.get("type"); target_string = condition.get("maxscript_property"); expected_value_str = condition.get("value"); error_msg = rule_data.get("error_message", "A rule failed.")
        if cond_type == "collection_property_all_match":
            collection_str = target_string; property_to_check = expected_value_str
            try:
                collection = rt.execute(collection_str); mismatched_objects = []
                for item in collection:
                    if rt.getProperty(item, property_to_check) == False: mismatched_objects.append(item.name)
                if mismatched_objects: error = f"{error_msg}: {', '.join(mismatched_objects)}"; return (False, error)
            except Exception as e: return (False, f"Error evaluating collection rule: {e}")
        else:
            if not target_string: return (False, f"Rule '{rule_data.get('name')}' has an empty target.")
            try: actual_value = rt.execute(target_string)
            except Exception as e: return (False, f"Error evaluating '{target_string}': {e}")
            if cond_type == "property_not_empty":
                if actual_value is None or str(actual_value).strip() == "": return (False, error_msg)
            elif cond_type == "min_value":
                try:
                    if float(actual_value) < float(expected_value_str): return (False, f"{error_msg} (Value: {actual_value}, Min: {expected_value_str})")
                except: return (False, "Invalid number in min_value rule.")
            elif cond_type == "max_value":
                try:
                    if float(actual_value) > float(expected_value_str): return (False, f"{error_msg} (Value: {actual_value}, Max: {expected_value_str})")
                except: return (False, "Invalid number in max_value rule.")
            elif cond_type == "property_equals":
                if str(actual_value).lower() != str(expected_value_str).lower(): return (False, f"{error_msg} (Value: {actual_value}, Expected: {expected_value_str})")
        return (True, "Passed")
        
# --- MainWindow and Main Execution ---
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("SceneLinter Pro"); self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint); self.resize(600, 500)
        self.ui_instance = SceneLinterProUI(self); self.setCentralWidget(self.ui_instance); self._create_menus()
    def _create_menus(self):
        menu_bar = self.menuBar(); help_menu = menu_bar.addMenu("Help")
        for name, url in LINKS.items():
            action = QtGui.QAction(name, self); action.triggered.connect(lambda checked=False, link=url: self._open_link(link)); help_menu.addAction(action)
        help_menu.addSeparator()
        about_action = QtGui.QAction("About SceneLinter Pro...", self); about_action.triggered.connect(self.show_about_dialog); help_menu.addAction(about_action)
    def _open_link(self, url): QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
    def show_about_dialog(self): about_dialog = AboutDialog(self); about_dialog.exec()
    def closeEvent(self, event):
        time.sleep(0.01)
        if self.ui_instance.is_dirty:
            reply = QtWidgets.QMessageBox.question(self, 'Unsaved Changes', "You have unsaved changes. Do you want to save before closing?", QtWidgets.QMessageBox.StandardButton.Save | QtWidgets.QMessageBox.StandardButton.Discard | QtWidgets.QMessageBox.StandardButton.Cancel, QtWidgets.QMessageBox.StandardButton.Cancel)
            if reply == QtWidgets.QMessageBox.StandardButton.Save:
                if self.ui_instance.save_rules_as(): event.accept()
                else: event.ignore()
            elif reply == QtWidgets.QMessageBox.StandardButton.Discard: event.accept()
            else: event.ignore()
        else: event.accept()

main_window_instance = None
def main():
    global main_window_instance
    try:
        if main_window_instance: main_window_instance.close(); main_window_instance.deleteLater()
    except: pass
    main_window_instance = MainWindow()
    main_window_instance.show()

if __name__ == "__main__":
    main()