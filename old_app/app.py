"""File Cache App — GUI and CLI entry point."""

from __future__ import annotations

import argparse
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from app.cache_manager import (
    cache_dir_for,
    cache_file,
    format_bytes,
    get_manifest,
    list_cached_files,
)
from app.file_reader import load_file_preview
from app.wrapper import (
    app_dir,
    clear_wrapper,
    get_wrapper,
    is_under_wrapper,
    list_wrapper_files,
    resolve_file,
    set_wrapper,
)


class FileCacheApp(tk.Tk):
    def __init__(self, initial_file: Path | None = None) -> None:
        super().__init__()
        self.title("File Cache App")
        self.geometry("900x640")
        self.minsize(720, 520)

        self._base = app_dir()
        self._file: Path | None = None
        if initial_file:
            try:
                self._file = resolve_file(initial_file, self._base)
            except FileNotFoundError:
                if initial_file.is_file():
                    self._file = initial_file.resolve()

        self._cancel_event = threading.Event()
        self._worker: threading.Thread | None = None
        self._busy = False
        self._wrapped_paths: list[Path] = []

        self._build_ui()
        self._refresh_wrapper_ui()
        if self._file:
            self._set_file(self._file)
            self._open_file_in_app(self._file)

    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 6}

        wrap_frame = ttk.LabelFrame(self, text="Folder Wrapper")
        wrap_frame.pack(fill=tk.X, **pad)

        wrap_row = ttk.Frame(wrap_frame)
        wrap_row.pack(fill=tk.X, padx=8, pady=6)

        ttk.Label(wrap_row, text="Target:").pack(side=tk.LEFT)
        self._wrapper_var = tk.StringVar(value="No folder wrapped")
        ttk.Entry(wrap_row, textvariable=self._wrapper_var, state="readonly").pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 6)
        )
        ttk.Button(wrap_row, text="Set Folder…", command=self._set_wrapper).pack(side=tk.LEFT)
        ttk.Button(wrap_row, text="Clear", command=self._clear_wrapper).pack(side=tk.LEFT, padx=(6, 0))

        self._wrapper_hint = ttk.Label(
            wrap_frame,
            text="Wrap a folder to browse and cache files inside it using relative paths.",
            foreground="#555",
        )
        self._wrapper_hint.pack(anchor=tk.W, padx=8, pady=(0, 6))

        top = ttk.Frame(self)
        top.pack(fill=tk.X, **pad)

        ttk.Label(top, text="File:").pack(side=tk.LEFT)
        self._file_var = tk.StringVar(value="No file selected")
        ttk.Entry(top, textvariable=self._file_var, state="readonly").pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 6)
        )
        ttk.Button(top, text="Browse…", command=self._browse).pack(side=tk.LEFT)
        ttk.Button(top, text="Open File", command=self._open_selected_file).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(top, text="Open Externally", command=self._open_externally).pack(side=tk.LEFT, padx=(6, 0))

        mid = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        mid.pack(fill=tk.BOTH, expand=True, **pad)

        wrapped_list = ttk.LabelFrame(mid, text="Files in Wrapped Folder")
        mid.add(wrapped_list, weight=1)

        self._wrapped_files = tk.Listbox(wrapped_list, exportselection=False)
        wrapped_scroll = ttk.Scrollbar(wrapped_list, orient=tk.VERTICAL, command=self._wrapped_files.yview)
        self._wrapped_files.configure(yscrollcommand=wrapped_scroll.set)
        self._wrapped_files.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=8)
        wrapped_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 8), pady=8)
        self._wrapped_files.bind("<Double-Button-1>", self._on_wrapped_open)
        self._wrapped_files.bind("<<ListboxSelect>>", self._on_wrapped_select)

        list_actions = ttk.Frame(wrapped_list)
        list_actions.pack(fill=tk.X, padx=8, pady=(0, 8))
        ttk.Button(list_actions, text="Open in App", command=self._open_from_list).pack(side=tk.LEFT)

        right = ttk.Frame(mid)
        mid.add(right, weight=2)

        notebook = ttk.Notebook(right)
        notebook.pack(fill=tk.BOTH, expand=True)
        self._notebook = notebook

        preview_frame = ttk.Frame(notebook)
        notebook.add(preview_frame, text="File Preview")

        self._preview = tk.Text(
            preview_frame, wrap=tk.NONE, state=tk.DISABLED, font=("Consolas", 10)
        )
        preview_y = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self._preview.yview)
        preview_x = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self._preview.xview)
        self._preview.configure(yscrollcommand=preview_y.set, xscrollcommand=preview_x.set)
        self._preview.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)
        preview_y.grid(row=0, column=1, sticky="ns", pady=8)
        preview_x.grid(row=1, column=0, sticky="ew", padx=(8, 0))
        preview_frame.rowconfigure(0, weight=1)
        preview_frame.columnconfigure(0, weight=1)

        self._preview_status = ttk.Label(
            preview_frame, text="Select a file and click Open File to view it here.", foreground="#555"
        )
        self._preview_status.grid(row=2, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 8))

        details_frame = ttk.Frame(notebook)
        notebook.add(details_frame, text="Cache Info")

        self._details = tk.Text(details_frame, height=8, wrap=tk.WORD, state=tk.DISABLED, font=("Consolas", 10))
        self._details.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        info = ttk.LabelFrame(self, text="Status")
        info.pack(fill=tk.X, **pad)

        self._status_var = tk.StringVar(value="Select a file, then click Cache File")
        ttk.Label(info, textvariable=self._status_var).pack(anchor=tk.W, padx=8, pady=4)

        self._cache_info_var = tk.StringVar(value="")
        ttk.Label(info, textvariable=self._cache_info_var, foreground="#555").pack(
            anchor=tk.W, padx=8, pady=(0, 6)
        )

        self._progress = ttk.Progressbar(info, mode="determinate")
        self._progress.pack(fill=tk.X, padx=8, pady=(0, 8))

        actions = ttk.Frame(self)
        actions.pack(fill=tk.X, **pad)
        self._cache_btn = ttk.Button(actions, text="Cache File", command=self._start_cache)
        self._cache_btn.pack(side=tk.LEFT)
        self._cancel_btn = ttk.Button(
            actions, text="Cancel", command=self._cancel, state=tk.DISABLED
        )
        self._cancel_btn.pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(actions, text="Open Cache Location", command=self._open_cache).pack(
            side=tk.LEFT, padx=(8, 0)
        )

        bottom = ttk.LabelFrame(self, text="Previously Cached Files")
        bottom.pack(fill=tk.BOTH, expand=False, **pad)
        self._history = tk.Listbox(bottom, height=3)
        self._history.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._history.bind("<Double-Button-1>", self._on_history_select)
        self._load_history()

    def _browse_initial_dir(self) -> str:
        wrapper = get_wrapper(self._base)
        if wrapper:
            return str(wrapper)
        if self._file:
            return str(self._file.parent)
        return str(Path.cwd())

    def _refresh_wrapper_ui(self) -> None:
        wrapper = get_wrapper(self._base)
        if wrapper:
            self._wrapper_var.set(str(wrapper))
            self._wrapper_hint.configure(
                text="Wrapped — pick a file from the list or browse inside this folder."
            )
        else:
            self._wrapper_var.set("No folder wrapped")
            self._wrapper_hint.configure(
                text="Wrap a folder to browse and cache files inside it using relative paths."
            )
        self._load_wrapped_files()

    def _load_wrapped_files(self) -> None:
        self._wrapped_files.delete(0, tk.END)
        self._wrapped_paths = []
        for rel, full in list_wrapper_files(self._base):
            self._wrapped_files.insert(tk.END, rel)
            self._wrapped_paths.append(full)

    def _on_wrapped_select(self, _event: tk.Event | None = None) -> None:
        sel = self._wrapped_files.curselection()
        if sel and sel[0] < len(self._wrapped_paths):
            self._set_file(self._wrapped_paths[sel[0]])

    def _on_wrapped_open(self, event: tk.Event) -> None:
        idx = self._wrapped_files.nearest(event.y)
        if 0 <= idx < len(self._wrapped_paths):
            self._open_file_in_app(self._wrapped_paths[idx])

    def _open_from_list(self) -> None:
        sel = self._wrapped_files.curselection()
        if sel and sel[0] < len(self._wrapped_paths):
            self._open_file_in_app(self._wrapped_paths[sel[0]])
            return
        messagebox.showinfo("Open File", "Select a file from the wrapped folder list.")

    def _open_selected_file(self) -> None:
        if not self._file or not self._file.is_file():
            messagebox.showinfo("Open File", "Select a file first.")
            return
        self._open_file_in_app(self._file)

    def _open_file_in_app(self, path: Path) -> None:
        self._set_file(path)
        try:
            content = load_file_preview(path)
        except OSError as exc:
            messagebox.showerror("Open File", str(exc))
            return

        self._preview.configure(state=tk.NORMAL)
        self._preview.delete("1.0", tk.END)
        self._preview.insert("1.0", content)
        self._preview.configure(state=tk.DISABLED)
        self._preview_status.configure(text=f"Viewing: {path.name}")
        self._notebook.select(0)
        self._status_var.set(f"Opened: {path.name}")

    def _open_externally(self) -> None:
        if not self._file or not self._file.is_file():
            messagebox.showinfo("Open Externally", "Select a file first.")
            return
        import os
        import subprocess

        path = self._file
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)

    def _set_wrapper(self) -> None:
        path = filedialog.askdirectory(initialdir=self._browse_initial_dir())
        if not path:
            return
        try:
            set_wrapper(Path(path), self._base)
        except NotADirectoryError as exc:
            messagebox.showerror("Wrapper Error", str(exc))
            return
        self._refresh_wrapper_ui()

    def _clear_wrapper(self) -> None:
        clear_wrapper(self._base)
        self._refresh_wrapper_ui()

    def _set_file(self, path: Path) -> None:
        self._file = path.resolve()
        wrapper = get_wrapper(self._base)
        if wrapper and is_under_wrapper(self._file, wrapper):
            rel = self._file.relative_to(wrapper).as_posix()
            self._file_var.set(rel)
        else:
            self._file_var.set(str(self._file))
        self._refresh_cache_info()

    def _browse(self) -> None:
        path = filedialog.askopenfilename(initialdir=self._browse_initial_dir())
        if path:
            self._set_file(Path(path))
            self._open_file_in_app(Path(path))

    def _refresh_cache_info(self) -> None:
        if not self._file:
            self._cache_info_var.set("")
            self._set_details("")
            return

        manifest = get_manifest(self._file)
        wrapper = get_wrapper(self._base)
        rel_line = ""
        if wrapper and is_under_wrapper(self._file, wrapper):
            rel_line = f"Relative: {self._file.relative_to(wrapper).as_posix()}\n"

        if manifest:
            self._cache_info_var.set(
                f"Cached {format_bytes(manifest.size)} at {manifest.cached_at}"
            )
            self._set_details(
                f"{rel_line}"
                f"Source:   {manifest.source_file}\n"
                f"Name:     {manifest.file_name}\n"
                f"Size:     {format_bytes(manifest.size)}\n"
                f"Modified: {manifest.modified}\n"
                f"Cached:   {manifest.cached_at}\n"
                f"SHA-256:  {manifest.sha256}\n"
                f"Location: {cache_dir_for(self._file)}"
            )
        else:
            self._cache_info_var.set("Not cached yet")
            self._set_details(f"{rel_line}Source: {self._file}\n\nThis file has not been cached.")

    def _set_details(self, text: str) -> None:
        self._details.configure(state=tk.NORMAL)
        self._details.delete("1.0", tk.END)
        self._details.insert("1.0", text)
        self._details.configure(state=tk.DISABLED)

    def _load_history(self) -> None:
        self._history.delete(0, tk.END)
        for item in list_cached_files():
            label = f"{item['source_file']} — {format_bytes(item['size'])}"
            self._history.insert(tk.END, label)

    def _on_history_select(self, _event: tk.Event) -> None:
        sel = self._history.curselection()
        if not sel:
            return
        files = list_cached_files()
        idx = sel[0]
        if idx < len(files):
            path = Path(files[idx]["source_file"])
            self._set_file(path)
            self._open_file_in_app(path)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        self._cache_btn.configure(state=state)
        self._cancel_btn.configure(state=tk.NORMAL if busy else tk.DISABLED)

    def _start_cache(self) -> None:
        if self._busy:
            return
        if not self._file or not self._file.is_file():
            messagebox.showerror("Error", "Select a file to cache first.")
            return

        self._cancel_event.clear()
        self._set_busy(True)
        self._progress["value"] = 0
        self._status_var.set("Caching file…")

        def worker() -> None:
            try:
                def on_progress(name: str, done: int, total: int) -> None:
                    pct = (done / total * 100) if total else 0
                    self.after(0, lambda: self._progress.configure(value=pct))
                    if name:
                        self.after(0, lambda n=name: self._status_var.set(f"Caching: {n}"))

                manifest = cache_file(
                    self._file,
                    on_progress=on_progress,
                    cancel_event=self._cancel_event,
                )
                self.after(0, lambda: self._on_cache_done(manifest))
            except InterruptedError:
                self.after(0, self._on_cache_cancelled)
            except Exception as exc:
                self.after(0, lambda: self._on_cache_error(exc))

        self._worker = threading.Thread(target=worker, daemon=True)
        self._worker.start()

    def _cancel(self) -> None:
        self._cancel_event.set()
        self._status_var.set("Cancelling…")

    def _on_cache_done(self, manifest) -> None:
        self._set_busy(False)
        self._progress["value"] = 100
        self._status_var.set(f"Done — cached {manifest.file_name} ({format_bytes(manifest.size)})")
        self._refresh_cache_info()
        self._load_history()

    def _on_cache_cancelled(self) -> None:
        self._set_busy(False)
        self._progress["value"] = 0
        self._status_var.set("Cancelled")
        self._refresh_cache_info()

    def _on_cache_error(self, exc: Exception) -> None:
        self._set_busy(False)
        self._progress["value"] = 0
        self._status_var.set("Error")
        messagebox.showerror("Cache Error", str(exc))

    def _open_cache(self) -> None:
        if not self._file:
            messagebox.showinfo("Cache", "Select a file first.")
            return
        path = cache_dir_for(self._file)
        if not path.exists():
            messagebox.showinfo("Cache", "No cache exists for this file yet.")
            return
        import os
        import subprocess

        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)


def _resolve_initial_file(args: argparse.Namespace, base: Path) -> Path | None:
    if args.file:
        try:
            return resolve_file(args.file, base)
        except FileNotFoundError:
            candidate = Path(args.file).resolve()
            return candidate if candidate.is_file() else None
    if len(sys.argv) >= 2 and not sys.argv[1].startswith("-"):
        candidate = Path(sys.argv[1])
        try:
            return resolve_file(candidate, base)
        except FileNotFoundError:
            return candidate.resolve() if candidate.is_file() else None
    return None


def run_cli(source: Path) -> int:
    print(f"Caching file: {source}")

    def on_progress(name: str, done: int, total: int) -> None:
        if name:
            print(f"  {name} ({done}/{total})")

    try:
        manifest = cache_file(source, on_progress=on_progress)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Done — {manifest.file_name}, {format_bytes(manifest.size)}")
    print(f"Cache location: {cache_dir_for(source)}")
    return 0


def main() -> int:
    base = app_dir()
    parser = argparse.ArgumentParser(
        description="Cache a single file into local storage. Optionally wrap a target folder."
    )
    parser.add_argument("file", nargs="?", help="File to cache (relative if a folder is wrapped)")
    parser.add_argument("--cli", action="store_true", help="Run without opening the GUI")
    parser.add_argument("--wrap", metavar="FOLDER", help="Wrap a target folder and save config")
    parser.add_argument("--wrap-clear", action="store_true", help="Remove the folder wrapper")
    parser.add_argument("--show-wrap", action="store_true", help="Print the wrapped folder path")
    args = parser.parse_args()

    if args.wrap_clear:
        clear_wrapper(base)
        print("Wrapper cleared.")
        return 0

    if args.wrap:
        try:
            config = set_wrapper(Path(args.wrap), base)
        except NotADirectoryError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(f"Wrapped folder: {config.target_folder}")
        if args.cli and args.file:
            source = _resolve_initial_file(args, base)
            if source and source.is_file():
                return run_cli(source)
        return 0

    if args.show_wrap:
        wrapper = get_wrapper(base)
        if wrapper:
            print(wrapper)
        else:
            print("No folder wrapped.")
        return 0

    source = _resolve_initial_file(args, base)

    if args.cli:
        if not source or not source.is_file():
            wrapper = get_wrapper(base)
            hint = "relative path inside wrapped folder" if wrapper else "file path"
            print(f"Error: provide a {hint} to cache.", file=sys.stderr)
            print("Usage: py app.py --cli path\\to\\file.txt", file=sys.stderr)
            if wrapper:
                print(f"Wrapped folder: {wrapper}", file=sys.stderr)
            return 1
        return run_cli(source)

    app = FileCacheApp(initial_file=source)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
