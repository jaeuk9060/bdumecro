# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for BDU LMS Tracker
Build command: pyinstaller build.spec
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로
project_root = Path(SPECPATH)
src_path = project_root / 'src'

a = Analysis(
    [str(src_path / 'main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # CustomTkinter 테마 파일 포함
    ],
    hiddenimports=[
        'customtkinter',
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.chrome.options',
        'webdriver_manager',
        'webdriver_manager.chrome',
        'bs4',
        'lxml',
        'lxml.etree',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='BDU_LMS_Tracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI 앱이므로 콘솔 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',  # 아이콘 파일이 있으면 주석 해제
)
