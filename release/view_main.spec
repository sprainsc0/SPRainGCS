# -*- mode: python ; coding: utf-8 -*-

block_cipher = pyi_crypto.PyiBlockCipher(key='anyway445')


a = Analysis(['view_main.py'],
             pathex=['C:\\Users\\Shan Gao\\Desktop\\PyGroundControl_e2'],
             binaries=[],
             datas=[],
             hiddenimports=['numpy.lib.twodim_base', 'tabs.tab_upgrade', 'tabs.tab_custom', 'tabs.tab_console', 'tabs.tab_plot', 'tabs.tab_calibrate', 'tabs.tab_sensors', 'PyQt5.uic', 'pyqtgraph.opengl', 'tabs.tab_params', 'tabs.tab_summary', 'lib.plot', 'lib.logAnalysis', 'lib.logdelegate', 'lib.serial_handle', 'qss_style', 'e2', 'tabs.tab_log'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='view_main',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True , icon='ccll.ico')
