from ctypes import *
from ctypes.wintypes import *
from enum import IntEnum
import sys
import logging

logger = logging.getLogger('J2DX.Windows.ViGEm')

try:
    vigem = cdll.LoadLibrary("ViGEmClient.dll")
except OSError:
    logger.critical("ViGEmBus driver not found. Please run 'j2dx --setup' first")
    sys.exit(1)

# Aggiunta costanti necessarie
XUSB_THUMB_MAX = 32767
XUSB_TRIGGER_MAX = 255

# Define necessary structures and constants
class VIGEM_ERRORS(IntEnum):
    VIGEM_ERROR_NONE = 0x20000000
    VIGEM_ERROR_ALREADY_CONNECTED = 0xE0000001
    VIGEM_ERROR_BUS_NOT_FOUND = 0xE0000002
    VIGEM_ERROR_NO_FREE_SLOT = 0xE0000003
    VIGEM_ERROR_INVALID_TARGET = 0xE0000004
    VIGEM_ERROR_REMOVAL_FAILED = 0xE0000005
    VIGEM_ERROR_LIB_VERSION_MISMATCH = 0xE0000006
    VIGEM_ERROR_BUS_VERSION_MISMATCH = 0xE0000007
    VIGEM_ERROR_BUS_ACCESS_FAILED = 0xE0000008
    VIGEM_ERROR_CALLBACK_ALREADY_REGISTERED = 0xE0000009
    VIGEM_ERROR_CALLBACK_NOT_FOUND = 0xE0000010
    VIGEM_ERROR_BUS_ALREADY_CONNECTED = 0xE0000011
    VIGEM_ERROR_BUS_INVALID_HANDLE = 0xE0000012
    VIGEM_ERROR_XUSB_USERINDEX_OUT_OF_RANGE = 0xE0000013
    VIGEM_ERROR_INVALID_PARAMETER = 0xE0000014

class XUSB_BUTTON(IntEnum):
    XUSB_GAMEPAD_DPAD_UP = 0x0001
    XUSB_GAMEPAD_DPAD_DOWN = 0x0002
    XUSB_GAMEPAD_DPAD_LEFT = 0x0004
    XUSB_GAMEPAD_DPAD_RIGHT = 0x0008
    XUSB_GAMEPAD_START = 0x0010
    XUSB_GAMEPAD_BACK = 0x0020
    XUSB_GAMEPAD_LEFT_THUMB = 0x0040
    XUSB_GAMEPAD_RIGHT_THUMB = 0x0080
    XUSB_GAMEPAD_LEFT_SHOULDER = 0x0100
    XUSB_GAMEPAD_RIGHT_SHOULDER = 0x0200
    XUSB_GAMEPAD_GUIDE = 0x0400
    XUSB_GAMEPAD_A = 0x1000
    XUSB_GAMEPAD_B = 0x2000
    XUSB_GAMEPAD_X = 0x4000
    XUSB_GAMEPAD_Y = 0x8000

class XUSB_REPORT(Structure):
    _fields_ = [
        ("wButtons", c_ushort),
        ("bLeftTrigger", c_ubyte),
        ("bRightTrigger", c_ubyte),
        ("sThumbLX", c_short),
        ("sThumbLY", c_short),
        ("sThumbRX", c_short),
        ("sThumbRY", c_short),
    ]

class DS4_BUTTONS(IntEnum):
    DS4_BUTTON_THUMB_RIGHT = 0x0001
    DS4_BUTTON_THUMB_LEFT = 0x0002
    DS4_BUTTON_OPTIONS = 0x0004
    DS4_BUTTON_SHARE = 0x0008
    DS4_BUTTON_TRIGGER_RIGHT = 0x0010
    DS4_BUTTON_TRIGGER_LEFT = 0x0020
    DS4_BUTTON_SHOULDER_RIGHT = 0x0040
    DS4_BUTTON_SHOULDER_LEFT = 0x0080
    DS4_BUTTON_TRIANGLE = 0x1000
    DS4_BUTTON_CIRCLE = 0x2000
    DS4_BUTTON_CROSS = 0x4000
    DS4_BUTTON_SQUARE = 0x8000

class DS4_SPECIAL_BUTTONS(IntEnum):
    DS4_SPECIAL_BUTTON_PS = 0x01
    DS4_SPECIAL_BUTTON_TOUCHPAD = 0x02

class DS4_DPAD_DIRECTIONS(IntEnum):
    DS4_BUTTON_DPAD_NONE = -1
    DS4_BUTTON_DPAD_NORTHWEST = 0
    DS4_BUTTON_DPAD_WEST = 1
    DS4_BUTTON_DPAD_SOUTHWEST = 2
    DS4_BUTTON_DPAD_SOUTH = 3
    DS4_BUTTON_DPAD_SOUTHEAST = 4
    DS4_BUTTON_DPAD_EAST = 5
    DS4_BUTTON_DPAD_NORTHEAST = 6
    DS4_BUTTON_DPAD_NORTH = 7

class DS4_REPORT(Structure):
    _fields_ = [
        ("bThumbLX", c_byte),
        ("bThumbLY", c_byte),
        ("bThumbRX", c_byte),
        ("bThumbRY", c_byte),
        ("wButtons", c_ushort),
        ("bSpecial", c_ubyte),
        ("bTriggerL", c_ubyte),
        ("bTriggerR", c_ubyte),
    ]

# Define function prototypes
vigem.alloc.restype = c_void_p
vigem.connect.argtypes = [c_void_p]
vigem.connect.restype = c_int
vigem.target_add.argtypes = [c_void_p, c_void_p]
vigem.target_add.restype = c_int
vigem.target_remove.argtypes = [c_void_p, c_void_p]
vigem.target_remove.restype = c_int
vigem.target_free.argtypes = [c_void_p]
vigem.disconnect.argtypes = [c_void_p]
vigem.free.argtypes = [c_void_p]
vigem.target_x360_alloc.restype = c_void_p
vigem.target_x360_update.argtypes = [c_void_p, c_void_p, POINTER(XUSB_REPORT)]
vigem.target_x360_update.restype = c_int
vigem.target_ds4_alloc.restype = c_void_p
vigem.target_ds4_update.argtypes = [c_void_p, c_void_p, POINTER(DS4_REPORT)]
vigem.target_ds4_update.restype = c_int
vigem.DS4_REPORT_INIT.argtypes = [POINTER(DS4_REPORT)]
vigem.DS4_SET_DPAD.argtypes = [POINTER(DS4_REPORT), c_int]
