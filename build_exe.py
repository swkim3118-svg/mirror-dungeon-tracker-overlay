import os
import shutil
import zipfile

import PyInstaller.__main__


APP_NAME = "MirrorDungeonTracker"
UPDATER_NAME = "Updater"


def build():
    for directory in ["build", "dist"]:
        if os.path.exists(directory):
            shutil.rmtree(directory)

    PyInstaller.__main__.run([
        "client/tracker_app.py",
        f"--name={APP_NAME}",
        "--windowed",
        "--add-data=data/mirror_dungeon.db;data",
        "--add-data=data/general_ego_gift_guide.md;data",
        "--add-data=data/egogift_icons;data/egogift_icons",
        "--hidden-import=ocr_client",
        "--hidden-import=screen_regions",
        "--hidden-import=sqlite3",
        "--icon=NONE",
        "--noconfirm",
    ])

    app_dir = os.path.join("dist", APP_NAME)
    exe_path = os.path.join(app_dir, f"{APP_NAME}.exe")
    readme_path = os.path.join(app_dir, "README.txt")
    version_path = os.path.join(app_dir, "VERSION.txt")
    zip_path = os.path.join("dist", f"{APP_NAME}.zip")
    version = os.environ.get("OVERLAY_VERSION", "dev")

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(
            "Mirror Dungeon Tracker Overlay\n"
            "\n"
            "1. Unzip MirrorDungeonTracker.zip first.\n"
            "2. Run Updater.exe from the extracted folder.\n"
            "3. Updater.exe installs updates and starts the overlay.\n"
            "4. The default server is http://54.198.45.77:8080.\n"
            "5. For local development, set MD_SERVER_URL before running the app.\n"
        )

    with open(version_path, "w", encoding="utf-8") as f:
        f.write(version + "\n")

    PyInstaller.__main__.run([
        "updater.py",
        f"--name={UPDATER_NAME}",
        "--onefile",
        "--windowed",
        "--icon=NONE",
        "--noconfirm",
    ])

    start_here_path = os.path.join("dist", "START_HERE.txt")
    with open(start_here_path, "w", encoding="utf-8") as f:
        f.write(
            "Mirror Dungeon Tracker Overlay\n"
            "\n"
            "Run Updater.exe to start the overlay.\n"
            "It automatically downloads the latest release when needed.\n"
        )

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(app_dir):
            for file_name in files:
                full_path = os.path.join(root, file_name)
                archive_path = os.path.relpath(full_path, "dist")
                zf.write(full_path, arcname=archive_path)
        zf.write(os.path.join("dist", f"{UPDATER_NAME}.exe"), arcname=f"{UPDATER_NAME}.exe")
        zf.write(start_here_path, arcname="START_HERE.txt")

    print(f"\nBuild complete: {exe_path}")
    print(f"Release zip: {zip_path}")


if __name__ == "__main__":
    build()
