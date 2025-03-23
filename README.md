# Video Selector & Tracker

A cross-platform desktop application built with PySide6 that allows you to randomly select, open, and track video files from a specified directory. The application features an adjustable bias slider to favor video selection from either the main directory or its subdirectories and includes a detailed history view with editable entries.


---

## Table of Contents

* [Features](#features)
* [Requirements](#requirements)
* [Installation](#installation)
* [Usage](#usage)
  * [Selecting Videos](#selecting-videos)
  * [Adjusting Selection Bias](#adjusting-selection-bias)
  * [Viewing and Editing History](#viewing-and-editing-history)
* [Project Structure](#project-structure)
* [Version Control](#version-control)
* [Contributing](#contributing)
* [License](#license)


---

## [Features](#features)

* **Random Video Selection:** \n Open a random video from a user-selected directory.
* **Bias Slider:** \n Adjust the probability of selecting videos from the main directory versus subdirectories.
  * *0*: Only main directory videos
  * *100*: Only subdirectory videos
  * In between values provide a weighted random selection.
* **Detailed History Dialog:** \n View a list of previously opened videos with:
  * Search functionality by video name.
  * Direct table cell editing for both video name (with file renaming) and rating.
  * Sorting of columns by clicking on the table headers.
  * Actions to delete, manually add, or undo deletion of entries via a drop-down cog menu.
* **Cross-Platform Compatibility:** \n Works on Windows, macOS, and Linux using system-specific commands to open video files.
* **Database Storage:** \n Uses an SQLite database for storing video history and user settings. The database is automatically copied to a writable location.


---

## [Requirements](#requirements)

* **Python:** Version 3.6 or later
* \*\*PySide6:\*\*For the GUI \n Install via pip:

  ```javascript
  bashCopypip install PySide6
  
  ```
* **SQLite3:** Comes with Python's standard library
* **Other Python Standard Libraries:** `os`, `sys`, `random`, `shutil`, `platform`, `subprocess`


---

## Installation


1. **Clone the Repository:**

   ```javascript
   bashCopygit clone https://github.com/your-organization/VideoSelector.git
   cd VideoSelector
   
   ```
2. **Create a Virtual Environment (Optional but Recommended):**

   ```javascript
   bashCopypython -m venv venv
   source venv/bin/activate   # On Windows use: venv\Scripts\activate
   
   ```
3. **Install Dependencies:**

   ```javascript
   bashCopypip install -r requirements.txt
   
   ```

   *(If you do not have a* `requirements.txt` file, ensure PySide6 is installed via `pip install PySide6`.)


---

## Usage

### Selecting Videos


1. **Launch the Application:**

   ```javascript
   bashCopypython your_script_name.py
   
   ```

   The main window displays a button labeled **"Open Random Video"** and a settings cog button.
2. **Select a Directory:**
   * Click the cog button and choose **"Select Directory"** to open a folder selection dialog.
   * The selected directory is saved and used for scanning video files.
3. **Open a Random Video:**
   * Click **"Open Random Video"** to have the app scan the selected directory.
   * The application then randomly selects and opens a video file using the default system application.

### Adjusting Selection Bias

* Use the slider located below the main controls to adjust the selection bias:
  * Drag the slider to **0** to favor videos only from the **main directory**.
  * Drag the slider to **100** to favor videos only from **subdirectories**.
  * The label updates in real time to show the current bias setting.

### Viewing and Editing History


1. **Open Detailed History:**
   * Click the cog button and select **"Open Detailed History"** to open the history dialog.
2. **Sorting and Searching:**
   * The history table is sortable by clicking on the **"Rating"** or **"Name"** column headers.
   * Use the search field to filter videos by name.
3. **Editing History Directly:**
   * You can click directly on a cell in the history table to edit a video's **rating** or **name**.
   * Changes are automatically saved to the SQLite database.
   * For name edits, the application attempts to rename the file on disk.
   * Additional actions such as **delete**, **add video manually**, and **undo deletion** are available through the cog menu in the history dialog.


---

## Project Structure

```javascript
bashCopyVideoSelector/
├── your_script_name.py      # Main application code (the provided code)
├── your_database.db         # (Bundled with the application; copied to a writable location)
├── README.md                # This file
└── .gitignore               # Git ignore rules for Python and PySide6 projects
```


---

## Version Control

This project uses Git for version control and GitHub for collaboration. A typical workflow is as follows:


1. **Initialize Repository (if not already done):**

   ```javascript
   bashCopygit init
   
   ```
2. **Stage and Commit Changes:**

   ```javascript
   bashCopygit add .
   git commit -m "Descriptive commit message"
   
   ```
3. **Push to GitHub:**

   ```javascript
   bashCopygit remote add origin https://github.com/your-organization/VideoSelector.git
   git push -u origin main
   
   ```
4. **Feature Branch and Pull Request:**
   * Create a feature branch:

     ```javascript
     bashCopygit checkout -b feature/slider-bias-control
     
     ```
   * Push your branch:

     ```javascript
     bashCopygit push -u origin feature/slider-bias-control
     
     ```
   * Create a pull request using the GitHub CLI:

     ```javascript
     bashCopygh pr create --title "Add slider for bias control" --body "Adds a slider to adjust video selection bias between main and subdirectories." --base main
     
     ```


---

## Contributing

Contributions are welcome! Please follow these guidelines:

* **Fork the Repository:** Create your own branch for new features or bug fixes.
* **Write Clear Commit Messages:** Follow a conventional commit style.
* **Submit Pull Requests:** Ensure your branch is up-to-date with `main` before submitting a pull request.
* **Code Reviews:** Be prepared to make changes based on peer review comments.


---

## License

This project is licensed under the MIT License.


---

*Happy coding and enjoy using Video Selector & Tracker!*