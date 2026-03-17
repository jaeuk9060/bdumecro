# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for BDU LMS Tracker
Build command: pyinstaller build.spec
Output: dist/BDU_LMS_Tracker/ (folder format)
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

# CustomTkinter 경로 가져오기
import customtkinter
ctk_path = Path(customtkinter.__file__).parent

# 프로젝트 루트 경로
project_root = Path(SPECPATH)
src_path = project_root / 'src'

# selenium 서브모듈 자동 수집 (누락 방지)
hiddenimports = [
    # CustomTkinter
    'customtkinter', 'customtkinter.windows', 'customtkinter.windows.widgets',
    'darkdetect', 'PIL', 'PIL._tkinter_finder',
    # BeautifulSoup / lxml
    'bs4', 'lxml', 'lxml.etree', 'lxml._elementpath',
    # 표준 라이브러리
    'json', 'logging', 'threading', 'dataclasses', 'pathlib', 're',
]
hiddenimports += collect_submodules('selenium')

a = Analysis(
    [str(src_path / 'main.py')],
    pathex=[str(project_root), str(src_path)],
    binaries=[],
    datas=[
        # CustomTkinter 테마/에셋 포함
        (str(ctk_path), 'customtkinter'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'pytest',
        'tkinter.test',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

# 폴더 형태 EXE (빠른 시작)
exe = EXE(
    pyz,
    a.scripts,
    [],  # binaries는 COLLECT로 분리
    exclude_binaries=True,
    name='BDU_LMS_Tracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI 앱 - 콘솔 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',  # 아이콘 파일이 있으면 주석 해제
)

# COLLECT - 폴더 형태 출력
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BDU_LMS_Tracker',
)
