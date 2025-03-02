# Joy2DroidX

Joy2DroidX allows you to use your Android device as a
virtual Xbox 360 controller or DualShock 4 gamepad.

It consists of a server that runs on Windows and Linux and an Flutter app running mostly everywhere. It's been only
tested on Android phones and on flutter web.


### Server

The server (this app) listens for input from connected
Android devices and manages creation/deletion of virtual devices.
It uses UInput on Linux and [ViGEm](https://github.com/ViGEm) on Windows.

While running the server *does not* require any special privileges, the initial setup (setting UInput permissions on Linux and installing driver on Windows) *requires root/administrator* access.

### Client

You can find more information about the Android app as well the sources [here](https://github.com/nik2208/joy_2_droid_x).


## Installation

At the moment, you can run the server using poetry and venv.

## Requirements

### Linux
- Python 3.8+
- uinput kernel module
- udev

### Windows (not updated yet)
- Python 3.8+
- ViGEmBus driver (installed automatically during setup)

## Installation

### Linux
```bash
python3 -m venv venv
poetry config virtualenvs.in-project true
poetry install
poetry run j2dx -d                 
```

### Windows (not updated yet)
```bash
pip install j2dx
j2dx --setup  # Requires admin privileges to install ViGEmBus
```

## Usage

### First run (not updated)

You need to setup the system before the first run.
Joy2DroidX provides a convenience command that does this for you, it however requires root/administrator access.

Just run `j2dx --setup` as root or from administrator command prompt.

On Linux this will create a udev rule for UInput and add current user to `j2dx` group. If you're not using sudo or user detection fails for another reason, you can provide username as an argument to `--setup`.
For udev rules and group changes to take effect you'll have to restart your system.

On Windows this will download [ViGEmBus driver](https://github.com/ViGEm/ViGEmBus) and prompt you to install it.
Once the driver is setup you can use Joy2DroidX, no restart necessary.

### Regular usage

Run `j2dx` (on windows you can just double click `j2dx.exe`), scan QRCode from the Android app and that's it.
Everything should just work. Switching device mode is done from the Android app.

The server should not need any extra configuration.
If you have an unsual network setup or default port is used by another process, there are a couple option you can modify:

- `-p, --port` allows you to use a different port. Default is 8013.
- `-H, --host` if hostname detection fails you can specify a hostname or your computers IP address.
- `-d, --debug` you shouldn't need this one. If you do encounter bugs, run `j2dx -d` and open an issue with a link to debug output (use a gist or pastebin for this).
