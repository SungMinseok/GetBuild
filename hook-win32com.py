# Custom PyInstaller hook to skip win32com
# This prevents PyInstaller from analyzing win32com module

from PyInstaller.utils.hooks import logger

logger.info("Custom hook: Skipping win32com module")

# Don't collect anything
hiddenimports = []

