# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
import os
import customtkinter

# 自动定位 customtkinter 主题资源目录，确保外观主题正常
customtkinter_path = os.path.dirname(customtkinter.__file__)

datas = [
    (customtkinter_path, 'customtkinter'),
]

a = Analysis(
    ['抓包分析工具.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'scapy.layers.all',
        'scapy.layers.http',
        'scapy.layers.inet',
        'scapy.layers.inet6',
        'scapy.layers.l2',
        'scapy.layers.dns',
        'scapy.layers.tls.record',
        'scapy.layers.tls.handshake',
        'scapy.layers.tls.extensions',
        'scapy.layers.tls.crypto',
        'scapy.layers.tls.session',
        'scapy.layers.tls.cert',
        'scapy.ansmachine',
        'scapy.as_resolvers',
        'scapy.asn1fields',
        'scapy.asn1packet',
        'scapy.automaton',
        'scapy.autorun',
        'scapy.base_classes',
        'scapy.compat',
        'scapy.config',
        'scapy.consts',
        'scapy.dadict',
        'scapy.data',
        'scapy.error',
        'scapy.fields',
        'scapy.interfaces',
        'scapy.main',
        'scapy.packet',
        'scapy.pipetool',
        'scapy.plist',
        'scapy.pton_ntop',
        'scapy.route',
        'scapy.route6',
        'scapy.scapypipes',
        'scapy.sendrecv',
        'scapy.sessions',
        'scapy.supersocket',
        'scapy.themes',
        'scapy.utils',
        'scapy.utils6',
        'scapy.volatile',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='抓包分析工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
