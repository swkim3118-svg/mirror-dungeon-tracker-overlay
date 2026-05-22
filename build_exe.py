import os
import shutil
import zipfile

import PyInstaller.__main__


APP_NAME = "MirrorDungeonTracker"


def build():
    for d in ["build", "dist"]:
        if os.path.exists(d):
            shutil.rmtree(d)

    PyInstaller.__main__.run([
        "client/tracker_app.py",
        f"--name={APP_NAME}",
        "--onefile",
        "--windowed",
        "--add-data=data/mirror_dungeon.db;data",
        "--hidden-import=ocr_client",
        "--hidden-import=screen_regions",
        "--hidden-import=sqlite3",
        "--icon=NONE",
        "--noconfirm",
    ])

    exe_path = os.path.join("dist", f"{APP_NAME}.exe")
    readme_path = os.path.join("dist", "README.txt")
    zip_path = os.path.join("dist", f"{APP_NAME}.zip")

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(
            "Mirror Dungeon Tracker Overlay\n"
            "\n"
            "1. MirrorDungeonTracker.exe를 실행하세요.\n"
            "2. 기본 서버는 EC2 본섭(http://3.83.159.179:8080)입니다.\n"
            "3. 로컬 개발 서버를 쓰려면 실행 전 MD_SERVER_URL 환경변수를 설정하세요.\n"
        )

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(exe_path, arcname=f"{APP_NAME}.exe")
        zf.write(readme_path, arcname="README.txt")

    print(f"\nBuild complete: {exe_path}")
    print(f"Release zip: {zip_path}")


if __name__ == "__main__":
    build()
