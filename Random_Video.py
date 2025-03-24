import os
import sys
import sqlite3
import random
import shutil
import platform
import subprocess

from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog, QLineEdit,
    QMessageBox, QLabel, QToolButton, QMenu, QTableWidget, QTableWidgetItem,
    QDialog, QWidgetAction, QHBoxLayout, QHeaderView, QSlider
)
from PySide6.QtCore import QDateTime, Qt
from PySide6.QtGui import QColor

# =============================================================================
# Utility Functions
# =============================================================================

def resource_path(relative_path):
    """
    Get the absolute path to a resource, whether running as a script or bundled via PyInstaller.
    """
    base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.abspath('.')
    return os.path.join(base_path, relative_path)


def get_writable_database_path():
    """
    Determine a writable location for the database based on the OS:
      - Windows: Uses LOCALAPPDATA/MyApp
      - Other OS: Uses ~/.myapp directory
    Copies the source database if needed.
    """
    if sys.platform == 'win32':
        base_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'MyApp')
    else:
        base_dir = os.path.expanduser('~/.myapp')
    os.makedirs(base_dir, exist_ok=True)
    
    writable_db_path = os.path.join(base_dir, 'your_database.db')
    source_db_path = resource_path('your_database.db')
    
    if not os.path.exists(source_db_path):
        print(f'Error: Source database not found at {source_db_path}.')
        sys.exit(1)
    
    if not os.path.exists(writable_db_path):
        print('Copying database to writable location...')
        shutil.copyfile(source_db_path, writable_db_path)
    
    return writable_db_path


# =============================================================================
# Global Initialization
# =============================================================================

db_path = get_writable_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS example (id INTEGER PRIMARY KEY, name TEXT)')
conn.commit()
print(f'Database is located at: {db_path}')


# =============================================================================
# Main Application Window
# =============================================================================
# Main application window for selecting, opening, and tracking videos.

class VideoSelector(QWidget):

    def __init__(self):
        super().__init__()
        self.last_deleted_entry = None
        self.selected_directory = ''
        self.current_video = ''
        self.selected_video_path = None
        
        # Set up UI and DB
        self.initUI()
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_db()
        self.load_last_directory()
        self.load_last_opened_video()
    
    def initUI(self):
        """
        Initialize the main window's UI, set up layouts, buttons, and style.
        """
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 1. Horizontal layout for "Open Random Video" and cog menu
        video_and_cog_layout = QHBoxLayout()
        video_and_cog_layout.setSpacing(10)
        
        self.open_video_btn = QPushButton('Open Random Video', self)
        self.open_video_btn.clicked.connect(self.open_random_video)
        video_and_cog_layout.addWidget(self.open_video_btn)
        
        self.cog_btn = QToolButton(self)
        self.cog_btn.setText('⚙')
        self.cog_btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.cog_btn.setPopupMode(QToolButton.InstantPopup)
        
        self.menu = QMenu(self)
        
        # Directory selection
        self.directory_btn = QPushButton('Select Directory', self)
        self.directory_btn.clicked.connect(self.select_directory)
        directory_action = QWidgetAction(self.menu)
        directory_action.setDefaultWidget(self.directory_btn)
        self.menu.addAction(directory_action)
        
        # Most recent file label
        self.recent_file_label = QLabel('Most Recent File: None', self)
        recent_file_action = QWidgetAction(self.menu)
        recent_file_action.setDefaultWidget(self.recent_file_label)
        self.menu.addAction(recent_file_action)
        
        # Detailed History
        history_btn = QPushButton('Open Detailed History', self)
        history_btn.clicked.connect(self.open_detailed_history)
        history_action_btn = QWidgetAction(self.menu)
        history_action_btn.setDefaultWidget(history_btn)
        self.menu.addAction(history_action_btn)
        
        self.cog_btn.setMenu(self.menu)
        video_and_cog_layout.addWidget(self.cog_btn)
        
        main_layout.addLayout(video_and_cog_layout)
        
        # 2. Slider + Label to control bias
        #    0 means "only main directory"
        #    100 means "only sub directories"
        bias_layout = QHBoxLayout()
        self.bias_label = QLabel("Directory Bias: 50")
        self.bias_slider = QSlider(Qt.Horizontal)
        self.bias_slider.setRange(0, 100)
        self.bias_slider.setValue(50)  # Default = balanced
        self.bias_slider.valueChanged.connect(self.on_bias_changed)
        
        bias_layout.addWidget(self.bias_label)
        bias_layout.addWidget(self.bias_slider)
        
        main_layout.addLayout(bias_layout)
        
        # Window properties
        self.setLayout(main_layout)
        self.setWindowTitle('Video Selector & Tracker (PySide6)')
        self.setFixedSize(400, 140)
        
        # Style
        self.setStyleSheet("""
            QWidget {
                background-color: #000;
                font-family: Arial, sans-serif;
                font-size: 12px;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0059;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QLabel {
                color: #fff;
            }
            QToolButton {
                background-color: transparent;
                font-size: 16px;
            }
            QTableWidget {
                gridline-color: #000;
            }
        """)
    
    def on_bias_changed(self, value):
        """
        Update label text whenever the slider value changes.
        """
        self.bias_label.setText(f"Directory Bias: {value}")
    
    def create_db(self):
        """
        Create the necessary database tables for video history and settings.
        """
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY,
                path TEXT,
                name TEXT,
                rating REAL,
                opened_at TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                key TEXT UNIQUE,
                value TEXT
            )
        ''')
        self.conn.commit()
    
    def load_last_directory(self):
        """
        Retrieve the last-used directory from the settings table.
        """
        self.cursor.execute('SELECT value FROM settings WHERE key = ?', ('last_directory',))
        result = self.cursor.fetchone()
        if result:
            self.selected_directory = result[0]
            self.directory_btn.setText(self.selected_directory)
        else:
            self.directory_btn.setText('Select Directory')
    
    def load_last_opened_video(self):
        """
        Retrieve and display the most recently opened video.
        """
        self.cursor.execute('SELECT name FROM videos ORDER BY opened_at DESC LIMIT 1')
        result = self.cursor.fetchone()
        if result:
            self.recent_file_label.setText(f'Most Recent File: {result[0]}')
    
    def select_directory(self):
        """
        Let the user choose a directory. Save this in the database for later use.
        """
        directory = QFileDialog.getExistingDirectory(self, 'Select Directory')
        if directory:
            self.selected_directory = directory
            self.directory_btn.setText(directory)
            self.cursor.execute(
                'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                ('last_directory', self.selected_directory)
            )
            self.conn.commit()
    
    def open_random_video(self):
        """
        Pick a random video from main directory or subdirectories
        based on the user's bias slider.
        """
        if not self.selected_directory:
            QMessageBox.warning(self, 'Error', 'Please select a directory first!')
            return
        
        # Separate files: main vs subdirectories
        main_videos = []
        sub_videos = []
        
        for root, _, files in os.walk(self.selected_directory):
            for file in files:
                if file.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):
                    # Check if the file is in the top-level (root == selected_directory)
                    if root == self.selected_directory:
                        main_videos.append(os.path.join(root, file))
                    else:
                        sub_videos.append(os.path.join(root, file))
        
        # If we have no videos at all:
        if not main_videos and not sub_videos:
            QMessageBox.warning(self, 'Error', 'No videos found in the selected directory!')
            return
        
        # Convert slider value to a 0..1 probability
        slider_val = self.bias_slider.value() / 100.0
        # Probability of picking from sub directories
        p_sub = slider_val
        # Probability of picking from main directory
        p_main = 1.0 - p_sub
        
        chosen = None
        # If main is empty, must pick from sub
        if not main_videos:
            chosen = random.choice(sub_videos)
        # If sub is empty, must pick from main
        elif not sub_videos:
            chosen = random.choice(main_videos)
        else:
            # Weighted pick
            if random.random() < p_main:
                chosen = random.choice(main_videos)
            else:
                chosen = random.choice(sub_videos)
        
        if chosen:
            print(f'Opening {chosen}')
            self.open_with_default_app(chosen)
            self.add_to_history(chosen)
    
    def open_with_default_app(self, file_path):
        """
        Open the given file using the system's default application.
        Supports macOS, Windows, and Linux.
        """
        if platform.system() == 'Darwin':
            subprocess.call(('open', file_path))
        elif platform.system() == 'Windows':
            os.startfile(file_path)
        else:
            subprocess.call(('xdg-open', file_path))
    
    def add_to_history(self, video_path):
        """
        Add the opened video to the history table and update the recent file display.
        """
        name = os.path.basename(video_path)
        opened_at = QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')
        self.cursor.execute(
            'INSERT INTO videos (path, name, rating, opened_at) VALUES (?, ?, ?, ?)',
            (video_path, name, None, opened_at)
        )
        self.conn.commit()
        self.recent_file_label.setText(f'Most Recent File: {name}')
    
    # -------------------------------------------------------------------------
    # DETAILED HISTORY DIALOG
    # -------------------------------------------------------------------------
    def open_detailed_history(self):
        """
        Open a dialog that displays the detailed history of opened videos.
        Provides search, delete, add, undo, update functionality,
        and now allows direct cell editing.
        """
        self.history_dialog = QDialog(self)
        self.history_dialog.setWindowTitle('Detailed History')
        self.history_dialog.setModal(True)
        
        history_layout = QVBoxLayout()
        history_layout.setSpacing(10)
        history_layout.setContentsMargins(10, 10, 10, 10)
        
        # Search input field
        self.search_input = QLineEdit(self.history_dialog)
        self.search_input.setPlaceholderText("Search by name...")
        self.search_input.textChanged.connect(self.update_history_table)
        history_layout.addWidget(self.search_input)
        
        # History table setup
        self.history_table = QTableWidget(self.history_dialog)
        self.history_table.setColumnCount(2)
        self.history_table.setHorizontalHeaderLabels(['Rating', 'Name'])
        self.history_table.setWordWrap(True)
        self.history_table.setColumnWidth(0, 50)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.history_table.setSortingEnabled(True)
        
        # Allow editing by adding the "editable" flag for items.
        # (The slot "cell_changed" will update the DB when the user makes changes.)
        self.history_table.cellChanged.connect(self.cell_changed)
        
        # Connect signals for selection/double-click actions.
        self.history_table.itemClicked.connect(self.select_video_for_editing)
        self.history_table.itemDoubleClicked.connect(self.open_selected_video)
        history_layout.addWidget(self.history_table)
        
        # Inputs below the table for reference (they're still available, but editing is now possible in the table too)
        self.rename_input = QLineEdit(self.history_dialog)
        self.rename_input.setPlaceholderText('Rename selected video')
        history_layout.addWidget(self.rename_input)
        
        self.rating_input = QLineEdit(self.history_dialog)
        self.rating_input.setPlaceholderText('Enter Rating (0.0 - 10.0)')
        history_layout.addWidget(self.rating_input)
        
        # Bottom row: Update Details button plus a cog button for extra actions.
        update_layout = QHBoxLayout()
        update_btn = QPushButton('Update Details', self.history_dialog)
        update_btn.clicked.connect(self.update_details)
        update_layout.addWidget(update_btn)
        
        actions_cog_btn = QToolButton(self.history_dialog)
        actions_cog_btn.setText('⚙')
        actions_cog_btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
        actions_cog_btn.setPopupMode(QToolButton.InstantPopup)
        update_layout.addWidget(actions_cog_btn)
        
        actions_menu = QMenu(self.history_dialog)
        delete_action = actions_menu.addAction('Delete Entry')
        delete_action.triggered.connect(self.delete_selected_entry)
        
        add_video_action = actions_menu.addAction('➕ Add Video Manually')
        add_video_action.triggered.connect(self.add_video_manually)
        
        undo_action = actions_menu.addAction('↩️ Undo Last Delete')
        undo_action.triggered.connect(self.undo_last_delete)
        
        actions_cog_btn.setMenu(actions_menu)
        history_layout.addLayout(update_layout)
        
        self.history_dialog.setLayout(history_layout)
        self.history_dialog.resize(600, 400)
        self.update_history_table()
        self.history_dialog.exec()

    def update_history_table(self):
        """
        Refresh the history table from the database.
        Block signals during update so that cellChanged events are not fired.
        """
        search_term = self.search_input.text().lower() if hasattr(self, 'search_input') else ''
        
        # Block signals to avoid triggering cell_changed while repopulating.
        self.history_table.blockSignals(True)
        self.history_table.setRowCount(0)
        
        self.cursor.execute('SELECT name, rating, path FROM videos ORDER BY opened_at DESC')
        history = self.cursor.fetchall()
        
        for name, rating, path in history:
            if search_term and search_term not in name.lower():
                continue
            
            row_position = self.history_table.rowCount()
            self.history_table.insertRow(row_position)
            
            # --- RATING COLUMN ---
            rating_item = QTableWidgetItem()
            if rating is not None:
                rating_item.setData(Qt.DisplayRole, float(rating))
                rating_item.setText(f'{rating:.1f}')
                rating_item.setForeground(self.get_color_for_rating(rating))
            else:
                rating_item.setData(Qt.DisplayRole, -1.0)
                rating_item.setText('N/A')
                rating_item.setForeground(QColor(128, 128, 128))
            # Make cell editable by adding Qt.ItemIsEditable
            rating_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
            self.history_table.setItem(row_position, 0, rating_item)
            
            # --- NAME COLUMN ---
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, path)  # Store full file path
            name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
            self.history_table.setItem(row_position, 1, name_item)
        
        self.history_table.blockSignals(False)

    def cell_changed(self, row, column):
        """
        Handle direct edits to a cell by updating the underlying database.
        For the rating column (0): update the rating.
        For the name column (1): update the video name and attempt to rename the file.
        """
        # Get the path stored in the "Name" cell's user data (same for every row)
        path_item = self.history_table.item(row, 1)
        if not path_item:
            return
        path = path_item.data(Qt.UserRole)
        if not path:
            return
        
        # Handle rating column edits
        if column == 0:
            new_rating_str = self.history_table.item(row, 0).text()
            try:
                new_rating = float(new_rating_str)
            except ValueError:
                QMessageBox.warning(self, 'Invalid Input', 'Rating must be a number.')
                # Restore previous value from DB
                self.history_table.blockSignals(True)
                self.cursor.execute('SELECT rating FROM videos WHERE path=?', (path,))
                result = self.cursor.fetchone()
                if result and result[0] is not None:
                    self.history_table.item(row, 0).setText(f'{result[0]:.1f}')
                else:
                    self.history_table.item(row, 0).setText('N/A')
                self.history_table.blockSignals(False)
                return
            
            # Update database with new rating
            self.cursor.execute('UPDATE videos SET rating = ? WHERE path = ?', (new_rating, path))
            self.conn.commit()
            # Update the cell color accordingly
            self.history_table.item(row, 0).setForeground(self.get_color_for_rating(new_rating))
        
        # Handle name column edits (video renaming)
        elif column == 1:
            new_name = self.history_table.item(row, 1).text()
            old_path = path
            video_dir = os.path.dirname(old_path)
            # Get the file extension from the old path
            _, file_ext = os.path.splitext(old_path)
            new_path = os.path.join(video_dir, new_name + file_ext)
            try:
                os.rename(old_path, new_path)
            except Exception as e:
                QMessageBox.warning(self, 'Rename Error', f'Error renaming file: {e}')
                # Reset the cell to its previous value from the DB
                self.history_table.blockSignals(True)
                self.cursor.execute('SELECT name FROM videos WHERE path=?', (old_path,))
                result = self.cursor.fetchone()
                if result:
                    self.history_table.item(row, 1).setText(result[0])
                self.history_table.blockSignals(False)
                return
            # Update database record with new name and new file path
            self.cursor.execute('UPDATE videos SET name = ?, path = ? WHERE path = ?', (new_name + file_ext, new_path, old_path))
            self.conn.commit()
            # Update the stored file path in the table's user data
            self.history_table.item(row, 1).setData(Qt.UserRole, new_path)
            # Also update the recent file label if applicable
            self.recent_file_label.setText(f'Most Recent File: {new_name + file_ext}')

    def get_color_for_rating(self, rating):
        """
        Calculate a color that goes from red (low rating) to green (high rating).
        """
        red = int((10 - rating) * 25.5)
        green = int(rating * 25.5)
        return QColor(red, green, 0)
    
    def select_video_for_editing(self, item):
        """
        When a row in the history table is clicked, populate the rename and rating fields.
        """
        row = item.row()
        self.selected_video_path = self.history_table.item(row, 1).data(Qt.UserRole)
        file_name, file_ext = os.path.splitext(os.path.basename(self.selected_video_path))
        self.rename_input.setText(file_name)
        self.selected_file_ext = file_ext
        
        current_rating = self.history_table.item(row, 0).text()
        if current_rating != 'N/A':
            self.rating_input.setText(current_rating)
        else:
            self.rating_input.clear()

    # Update the video's name (by renaming the file) and its rating in the database.
    def update_details(self):

        new_name = self.rename_input.text()
        rating_text = self.rating_input.text()
        
        if self.selected_video_path and new_name:
            video_dir = os.path.dirname(self.selected_video_path)
            new_path = os.path.join(video_dir, new_name + self.selected_file_ext)
            os.rename(self.selected_video_path, new_path)
            self.cursor.execute(
                'UPDATE videos SET name = ?, path = ? WHERE path = ?',
                (new_name + self.selected_file_ext, new_path, self.selected_video_path)
            )
            self.conn.commit()
            self.selected_video_path = new_path
        
        try:
            rating = float(rating_text) if rating_text else None
        except ValueError:
            QMessageBox.warning(self, 'Invalid Input', 'Rating must be a number.')
            return
        else:
            if self.selected_video_path:
                self.cursor.execute(
                    'UPDATE videos SET rating = ? WHERE path = ?',
                    (rating, self.selected_video_path)
                )
                self.conn.commit()
        
        QMessageBox.information(self, 'Success', 'Details updated successfully!')
        self.update_history_table()
        self.rename_input.clear()
        self.rating_input.clear()
    
    def open_selected_video(self, item):
        """
        Open the video file corresponding to a double-clicked history entry.
        """
        row = item.row()
        video_path = self.history_table.item(row, 1).data(Qt.UserRole)
        if video_path:
            self.open_with_default_app(video_path)
    
    def delete_selected_entry(self):
        """
        Delete the currently selected video entry from the history database.
        (This does not remove the actual video file from disk.)
        """
        if not self.selected_video_path:
            QMessageBox.warning(self, 'No Selection', 'Please select a video entry to delete.')
            return
        
        confirm = QMessageBox.question(
            self, 'Confirm Deletion',
            'Are you sure you want to delete this entry from history? This will not delete the video file.',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.cursor.execute(
                'SELECT name, rating, path, opened_at FROM videos WHERE path = ?',
                (self.selected_video_path,)
            )
            self.last_deleted_entry = self.cursor.fetchone()
            
            self.cursor.execute('DELETE FROM videos WHERE path = ?', (self.selected_video_path,))
            self.conn.commit()
            
            QMessageBox.information(self, 'Deleted', 'Entry deleted from history.')
            self.selected_video_path = None
            self.rename_input.clear()
            self.rating_input.clear()
            self.update_history_table()
    
    def undo_last_delete(self):
        """
        Restore the last deleted video entry back into the history.
        """
        if self.last_deleted_entry:
            name, rating, path, opened_at = self.last_deleted_entry
            self.cursor.execute(
                'INSERT INTO videos (name, rating, path, opened_at) VALUES (?, ?, ?, ?)',
                (name, rating, path, opened_at)
            )
            self.conn.commit()
            QMessageBox.information(self, 'Undo', f'"{name}" has been restored to history.')
            self.last_deleted_entry = None
            self.update_history_table()
        else:
            QMessageBox.information(self, 'Nothing to Undo', 'No deleted entry to restore.')
    
    def add_video_manually(self):
        """
        Allow the user to manually add a video file to the history via a file dialog.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Select Video File',
            '',
            'Video Files (*.mp4 *.avi *.mkv *.mov)'
        )
        
        if file_path:
            name = os.path.basename(file_path)
            opened_at = QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')
            self.cursor.execute(
                'INSERT INTO videos (path, name, rating, opened_at) VALUES (?, ?, ?, ?)',
                (file_path, name, None, opened_at)
            )
            self.conn.commit()
            QMessageBox.information(self, 'Added', f'"{name}" was added to the history.')
            self.update_history_table()

    def test(self):
        print('test')

# =============================================================================
# Application Entry Points
# =============================================================================

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VideoSelector()
    window.show()
    sys.exit(app.exec())
