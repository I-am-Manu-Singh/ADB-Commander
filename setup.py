from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'app_icon.icns',
    'packages': ['PIL', 'tkinterdnd2'],
    'includes': ['tkinter', 'queue', 'threading', 'subprocess', 'shutil', 'tempfile', 'os', 're'],
    'plist': {
        'CFBundleName': 'ADB Commander',
        'CFBundleDisplayName': 'ADB Commander',
        'CFBundleIdentifier': "com.manu_singh.adbglass",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0",
        'NSRequiresAquaSystemAppearance': False,
        'LSMinimumSystemVersion': '10.13.0',
    }
}

setup(
    app=APP,
    name='ADB Commander',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
