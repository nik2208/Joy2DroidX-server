import os
import sys
import logging
import winreg
from urllib.request import urlopen
from tempfile import NamedTemporaryFile
from ctypes import windll, c_void_p, c_wchar_p, c_int

VIGEM_REL = 'https://github.com/ViGEm/ViGEmBus/releases'
VIGEM_URI = f'{VIGEM_REL}/download/v1.17.333/ViGEmBus_Setup_1.17.333.exe'

SE_ERR_ACCESSDENIED = 5
SUCCESS = lambda errno: errno > 32    # noqa

ShellExecuteW = windll.shell32.ShellExecuteW
ShellExecuteW.argtypes = (
    c_void_p, c_wchar_p, c_wchar_p, c_wchar_p, c_wchar_p, c_int)
ShellExecuteW.restype = c_int

logger = logging.getLogger('J2DX.Windows.Setup')

def check_vigem_installed():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Services\ViGEmBus",
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY
        )
        winreg.CloseKey(key)
        return True
    except WindowsError:
        return False

def setup(user=None):
    if check_vigem_installed():
        logger.info("ViGEmBus driver is already installed")
        return

    logger.info('Setting up ViGEmBus driver for Windows')
    with NamedTemporaryFile(
            delete=False, prefix='ViGEmBus-', suffix='.exe') as tmp:
        logger.info('Downloading compatible ViGEmBus driver')
        try:
            resp = urlopen(VIGEM_URI)
            tmp.write(resp.read())
            tmp.flush()
            vigembus = tmp.name
        except OSError as e:
            logger.critical(f'Driver download failed. Error {e.errno}')
            logger.info(
                f'Please manually download latest driver from {VIGEM_REL}')
            sys.exit(e.errno)

    logger.info('Running setup. Please accept UAC prompt when it appears.')
    ret = ShellExecuteW(
        None, 'runas',
        vigembus, '/quiet /promptrestart',
        None, 1)

    try:
        os.unlink(vigembus)
    except:
        pass

    if SUCCESS(ret):
        logger.info(
            'Setup complete. '
            'You may need to reboot before you can use virtual device driver.')
        sys.exit(0)
    else:
        if ret == SE_ERR_ACCESSDENIED:
            logger.critical('Setup needs administrator access to install drivers.')
        else:
            logger.critical(f'Unexpected error: {ret}')
        sys.exit(ret)
