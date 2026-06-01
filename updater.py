import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from tkinter import Label, Tk, messagebox


APP_NAME = "MirrorDungeonTracker"
RELEASE_API = (
    "https://api.github.com/repos/swkim3118-svg/"
    "mirror-dungeon-tracker-overlay/releases/latest"
)


def root_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.dirname(__file__))


def app_dir():
    return os.path.join(root_dir(), APP_NAME)


def app_exe():
    return os.path.join(app_dir(), f"{APP_NAME}.exe")


def read_local_version():
    try:
        with open(os.path.join(app_dir(), "VERSION.txt"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def get_latest_release():
    request = urllib.request.Request(
        RELEASE_API,
        headers={"Accept": "application/vnd.github+json", "User-Agent": APP_NAME},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        release = json.load(response)
    asset = next(
        item for item in release.get("assets", [])
        if item.get("name") == f"{APP_NAME}.zip"
    )
    return release["tag_name"], asset["browser_download_url"]


def install_latest(download_url, show_status):
    with tempfile.TemporaryDirectory(prefix="mirror-dungeon-update-") as temp_dir:
        zip_path = os.path.join(temp_dir, f"{APP_NAME}.zip")
        extract_dir = os.path.join(temp_dir, "extract")
        show_status("Downloading latest overlay... 0%")

        def report_progress(block_count, block_size, total_size):
            if total_size > 0:
                progress = min(100, block_count * block_size * 100 // total_size)
                show_status(f"Downloading latest overlay... {progress}%")

        urllib.request.urlretrieve(download_url, zip_path, reporthook=report_progress)
        show_status("Installing latest overlay...")
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_dir)

        source_dir = os.path.join(extract_dir, APP_NAME)
        source_exe = os.path.join(source_dir, f"{APP_NAME}.exe")
        if not os.path.isfile(source_exe):
            raise RuntimeError("Downloaded update is missing the overlay executable.")
        shutil.copytree(source_dir, app_dir(), dirs_exist_ok=True)


def launch_overlay():
    if not os.path.isfile(app_exe()):
        raise RuntimeError("MirrorDungeonTracker.exe was not found.")
    subprocess.Popen([app_exe()], cwd=app_dir())


def main():
    window = Tk()
    window.title("Mirror Dungeon Tracker Updater")
    window.geometry("340x80")
    window.resizable(False, False)
    label = Label(window, text="", padx=18, pady=22)
    label.pack()
    window.withdraw()

    def show_status(text):
        label.config(text=text)
        window.deiconify()
        window.update_idletasks()

    try:
        latest_version, download_url = get_latest_release()
        if read_local_version() != latest_version:
            install_latest(download_url, show_status)
        window.withdraw()
        launch_overlay()
    except PermissionError:
        messagebox.showerror(
            "Mirror Dungeon Tracker",
            "Close the running overlay, then run Updater.exe again.",
        )
    except Exception as exc:
        if os.path.isfile(app_exe()):
            launch_existing = messagebox.askyesno(
                "Mirror Dungeon Tracker",
                f"Update check failed.\n\n{exc}\n\nRun the installed overlay anyway?",
            )
            if launch_existing:
                launch_overlay()
        else:
            messagebox.showerror("Mirror Dungeon Tracker", str(exc))
    finally:
        window.destroy()


if __name__ == "__main__":
    main()
