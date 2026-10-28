# File Cache App

A portable Python app that caches **one selected file at a time** into local storage. It can also act as a **wrapper** over any folder you choose — browse files inside that folder, use relative paths on the command line, and cache them without typing full paths.

No external dependencies — uses Python 3.10+ and the standard library only.

## Requirements

- **Python 3.10 or newer**
- **tkinter** (included with most Python installs; needed for the GUI)

Check your install:

```powershell
py --version
```

## Quick start

### GUI

```powershell
py app.py
```

This opens a window where you can:

- **Set Folder…** to wrap a target folder (saved in `wrapper.json`)
- Pick files from the **Files in Wrapped Folder** list (single-click to select, double-click to open)
- Click **Open File** or **Open in App** to view a file inside the app
- Click **Open Externally** to open the file in your default system app
- Select a file with **Browse…**
- Click **Cache File** to copy it into the cache
- View cache details (size, hash, location)
- Click **Open Cache Location** to open the cache folder in Explorer
- Double-click a file in **Previously Cached Files** to load it

### Command line

Cache a specific file:

```powershell
py app.py --cli "C:\path\to\your\file.txt"
```

## Folder wrapper

The app directory can wrap any folder on your system. When wrapped:

- The GUI lists all files inside the target folder
- **Browse…** opens inside the wrapped folder
- CLI accepts **relative paths** (e.g. `report.pdf` instead of the full path)
- The config is stored in `wrapper.json` next to the app

### Set a wrapper (CLI)

```powershell
py app.py --wrap "C:\Projects\MyProject"
```

Cache a file using a relative path:

```powershell
py app.py --cli "src\main.py"
```

Show the current wrapper:

```powershell
py app.py --show-wrap
```

Clear the wrapper:

```powershell
py app.py --wrap-clear
```

### Set a wrapper (GUI or batch file)

- Click **Set Folder…** in the GUI, or
- Run **`WrapFolder.bat "C:\Projects\MyProject"`**, or
- Drag a folder onto **`WrapFolder.bat`**

Copy the whole `folder_cache` directory anywhere — the wrapper config travels with it and still points at your target folder.

## Ways to use it

### Option 1 — Run from anywhere (recommended)

Keep the app in one place and pass the file path as an argument:

```powershell
py D:\path\to\folder_cache\app.py --cli "C:\Projects\report.pdf"
```

Or open the GUI with a file pre-selected:

```powershell
py D:\path\to\folder_cache\app.py "C:\Projects\report.pdf"
```

### Option 2 — Drag and drop (Windows)

Drag a file onto **`CacheDroppedFile.bat`**. The app caches that file and shows progress in the terminal.

Run **`CacheDroppedFile.bat`** with no arguments to open the GUI instead.

### Option 3 — Right-click any file (Windows)

Run **`InstallOpenWith.bat`** once. After that, right-click any file and choose **Open with File Cache App** to open it in the GUI with preview/cache actions ready.

Run **`UninstallOpenWith.bat`** to remove the menu entry.

### Option 4 — Launch from the app directory

- **`CacheFolder.bat`** — opens the GUI (Windows)
- **`cache-folder.sh`** — opens the GUI (Linux/macOS)

## Where caches are stored

Caches are saved outside the source folder so your project directory stays clean:

| Platform | Location |
|----------|----------|
| Windows  | `%LOCALAPPDATA%\FolderCacheApp\caches\` |
| macOS/Linux | `~/FolderCacheApp/caches/` (or `$HOME`) |

Each cached file gets its own subdirectory keyed by the file's full path. Inside you'll find:

```
caches/
  <hash>/
    manifest.json    # metadata for the cached file
    report.pdf       # copy of the original file
```

### manifest.json

The manifest records:

- Original source file path
- File name
- When the cache was created
- File size and last modified time
- SHA-256 hash of the cached copy

Re-caching the same file **replaces** the previous cache for that path.

## File overview

| File | Purpose |
|------|---------|
| `app.py` | GUI and CLI entry point |
| `cache_manager.py` | Copying and manifest logic |
| `wrapper.py` | Folder wrapper config and path resolution |
| `file_reader.py` | In-app text preview for wrapped files |
| `wrapper.json` | Saved wrapper target (created when you set a folder) |
| `WrapFolder.bat` | Set wrapper and open GUI (Windows) |
| `CacheDroppedFile.bat` | Drag-and-drop or GUI launcher (Windows) |
| `OpenWithFileCache.bat` | Open a selected file in the GUI (Windows) |
| `InstallOpenWith.bat` | Add right-click menu entry for all files (Windows) |
| `UninstallOpenWith.bat` | Remove right-click menu entry (Windows) |
| `CacheFolder.bat` | Open GUI from the app directory (Windows) |
| `cache-folder.sh` | Open GUI from the app directory (Linux/macOS) |

## Tips

- **One file at a time** — select or pass a single file path; folders are not cached as a whole.
- **Wrapper mode** — set a target folder once, then work with relative paths and the built-in file list.
- **In-app preview** — open text files from the wrapped folder in the **File Preview** tab (up to 512 KB shown; binary files show a short notice instead).
- **Re-cache to refresh** — click **Cache File** again to update the cache with the latest version.
- **History** — the GUI lists previously cached files at the bottom; double-click to load one.
- **Large files** — caching runs in a background thread in the GUI. Use **Cancel** to stop mid-run.

## Troubleshooting

**"Python is not installed or not on PATH"** (batch files)

Install Python from [python.org](https://www.python.org/downloads/) and enable **Add Python to PATH** during setup. On Windows you can also try `py` instead of `python`.

**GUI does not open**

Your Python build may not include tkinter. Reinstall Python and ensure tcl/tk is included, or use `--cli` mode instead.

**"Not a file" error**

You passed a folder or a path that does not exist. Provide the full path to a single file.

**Permission errors**

The source file must be readable and the cache directory must be writable (usually `%LOCALAPPDATA%` on Windows).

## Example

```powershell
py app.py --cli "D:\untitled\folder_cache\README.md"
```

Output:

```
Caching file: D:\untitled\folder_cache\README.md
  README.md (1/1)
Done — README.md, 4.2 KB
Cache location: C:\Users\You\AppData\Local\FolderCacheApp\caches\a1b2c3d4e5f67890
```
