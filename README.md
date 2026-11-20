# AuroraDVD

Modern DVD Player for Windows 11

## Estado

🚧 En desarrollo

## Versión

0.1.0-dev

## Tecnologías

- Python
- PySide6
- VLC

## Compilar el ZIP portable para Windows x64

Para usar AuroraDVD, extrae el ZIP completo y abre `AuroraDVD.exe`. El ZIP
incluye Python, Qt y LibVLC.

Para generar el ZIP, usa Python x64 en Windows y extrae un ZIP oficial de VLC
para Windows x64. Con el entorno virtual del proyecto activo, ejecuta:

```powershell
python -m pip install -e . pyinstaller==6.22.3
python installer/build_portable.py --vlc-dir 'C:\ruta\vlc-3.0.24'
```

También puedes pasar la carpeta de VLC instalado mediante `--vlc-dir`.
El archivo `dist/AuroraDVD-portable-win-x64.zip` se puede adjuntar como
artefacto a una Release de GitHub. La compilación conserva el ejecutable y
la carpeta `LibVLC` juntos dentro del ZIP.
