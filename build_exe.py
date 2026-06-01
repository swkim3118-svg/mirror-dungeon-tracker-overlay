import os
import shutil
import zipfile

import PyInstaller.__main__


APP_NAME = "MirrorDungeonTracker"


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
    zip_path = os.path.join("dist", f"{APP_NAME}.zip")

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(
            "Mirror Dungeon Tracker Overlay\n"
            "\n"
            "1. Unzip MirrorDungeonTracker.zip first.\n"
            "2. Keep all files in the extracted MirrorDungeonTracker folder.\n"
            "3. Run MirrorDungeonTracker.exe inside that folder.\n"
            "4. The default server is http://13.218.132.41:8080.\n"
            "5. For local development, set MD_SERVER_URL before running the app.\n"
        )

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(app_dir):
            for file_name in files:
                full_path = os.path.join(root, file_name)
                archive_path = os.path.relpath(full_path, "dist")
                zf.write(full_path, arcname=archive_path)

    print(f"\nBuild complete: {exe_path}")
    print(f"Release zip: {zip_path}")


if __name__ == "__main__":
    build()
