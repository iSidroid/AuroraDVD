"""Build the portable Windows x64 ZIP from a VLC installation or official ZIP."""

import argparse
import shutil
import subprocess
import sys
import sysconfig
import zipfile
from importlib import metadata
from pathlib import Path

import pefile


ROOT = Path(__file__).resolve().parents[1]
APP_NAME = "AuroraDVD"
ARCHIVE_NAME = "AuroraDVD-portable-win-x64.zip"


def validate_vlc(vlc_dir: Path) -> str:
    for name in ("libvlc.dll", "libvlccore.dll"):
        library = vlc_dir / name
        if not library.is_file():
            raise ValueError(f"Missing VLC library: {library}")
        dll = pefile.PE(str(library), fast_load=False)
        try:
            if dll.FILE_HEADER.Machine != pefile.MACHINE_TYPE["IMAGE_FILE_MACHINE_AMD64"]:
                raise ValueError(f"Expected a Windows x64 VLC library: {library}")
            version = dll.VS_FIXEDFILEINFO[0]
        finally:
            dll.close()
    if not (vlc_dir / "plugins/access/libdvdnav_plugin.dll").is_file():
        raise ValueError(f"Missing VLC DVD module under {vlc_dir / 'plugins'}")
    return ".".join(str(value) for value in (
        version.FileVersionMS >> 16,
        version.FileVersionMS & 0xFFFF,
        version.FileVersionLS >> 16,
    ))


def freeze_app(work_dir: Path) -> Path:
    icon = ROOT / "src/auroradvd/resources/auroradvd.ico"
    icon_options = ["--icon", str(icon)] if icon.is_file() else []
    subprocess.run(
        [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm", "--onedir", "--windowed", "--noupx",
            "--name", APP_NAME,
            "--add-data", f"{ROOT / 'src/auroradvd/resources'}:auroradvd/resources",
            *icon_options,
            "--paths", str(ROOT / "src"),
            "--specpath", str(work_dir),
            "--workpath", str(work_dir / "pyinstaller"),
            "--distpath", str(work_dir / "dist"),
            str(ROOT / "src/auroradvd/__main__.py"),
        ],
        check=True,
        cwd=ROOT,
    )
    app_dir = work_dir / "dist" / APP_NAME
    # The Qt Windows wheel uses the Windows ICU ABI. Dependency analysis can
    # pick up an incompatible unversioned ICU DLL from the builder's PATH.
    for name in ("icu.dll", "icuin.dll", "icuuc.dll"):
        (app_dir / "_internal" / name).unlink(missing_ok=True)
    return app_dir


def stage_vlc(app_dir: Path, vlc_dir: Path) -> None:
    target = app_dir / "LibVLC"
    target.mkdir()
    for name in ("libvlc.dll", "libvlccore.dll", "COPYING.txt", "AUTHORS.txt", "THANKS.txt"):
        source = vlc_dir / name
        if source.is_file():
            shutil.copy2(source, target)
    for name in ("plugins", "lua", "hrtfs"):
        source = vlc_dir / name
        if source.is_dir():
            shutil.copytree(source, target / name)


def stage_notices(app_dir: Path, version: str) -> None:
    notices = app_dir / "Licencias"
    notices.mkdir()
    for name in ("python-vlc", "psutil", "PySide6-Essentials", "shiboken6", "PyInstaller"):
        distribution = metadata.distribution(name)
        for file in distribution.files or ():
            if file.name.lower().startswith(("copying", "license", "notice")) and ".dist-info" in str(file):
                target = notices / name / file.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(distribution.locate_file(file), target)
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    if python_license.is_file():
        shutil.copy2(python_license, notices / "Python-LICENSE.txt")

    qt = metadata.version("PySide6-Essentials")
    bindings = metadata.version("python-vlc")
    (notices / "Componentes.txt").write_text(
        f"LibVLC y módulos de VideoLAN {version}. Consulta LibVLC/COPYING.txt.\n"
        f"Código fuente de VideoLAN: https://download.videolan.org/pub/videolan/vlc/{version}/\n"
        f"Licencia de LibVLC: https://github.com/videolan/vlc/blob/{version}/COPYING.LIB\n"
        f"Qt y PySide6 {qt}: https://download.qt.io/official_releases/qt/{qt.rsplit('.', 1)[0]}/{qt}/\n"
        f"Licencias de Qt: https://github.com/qt/qtbase/tree/v{qt}/LICENSES\n"
        f"python-vlc {bindings}: https://pypi.org/project/python-vlc/{bindings}/\n",
        encoding="utf-8",
    )
    (app_dir / "LEEME.txt").write_text(
        "AuroraDVD portable para Windows x64\n\n"
        "Extrae el ZIP completo y ejecuta AuroraDVD.exe.\n"
        "Mantén las carpetas LibVLC y _internal junto al ejecutable.\n"
        "Para reproducir un disco, elige Archivo > Abrir DVD y selecciona la unidad.\n"
        "Esta compilación incluye Python, Qt y el motor LibVLC.\n"
        "Los avisos de los componentes se encuentran en Licencias y LibVLC.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vlc-dir", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, default=ROOT / "build/portable")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    if sysconfig.get_platform() != "win-amd64":
        parser.error("Build this package with Windows x64 Python.")

    vlc_dir = args.vlc_dir.resolve()
    try:
        version = validate_vlc(vlc_dir)
    except (ValueError, pefile.PEFormatError, AttributeError, IndexError) as error:
        parser.error(str(error))

    work_dir = args.work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    app_dir = freeze_app(work_dir)
    stage_vlc(app_dir, vlc_dir)
    stage_notices(app_dir, version)

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / ARCHIVE_NAME
    temporary = output_dir / (ARCHIVE_NAME + ".tmp")
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
            for file in sorted(app_dir.rglob("*")):
                if file.is_file():
                    bundle.write(file, file.relative_to(app_dir.parent).as_posix())
        temporary.replace(archive)
    finally:
        temporary.unlink(missing_ok=True)
    print(archive)


if __name__ == "__main__":
    main()
