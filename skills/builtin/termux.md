---
name: termux
version: 1.0.0
description: Termux environment mastery  - packages, storage, environments, troubleshooting
author: pocketclaw
layer: 1
category: core
---

# Termux Environment Guide

You are running inside Termux on Android. This is NOT a standard Linux box.
Memorise these differences  - they matter for every command you run.

## Key Paths

- Home: `/data/data/com.termux/files/home` (or just `~`)
- Prefix: `/data/data/com.termux/files/usr` (equivalent of `/usr`)
- Shared storage: `~/storage/shared` (Android's internal storage, needs `termux-setup-storage`)
- Downloads: `~/storage/downloads`
- DCIM/photos: `~/storage/dcim`
- SD card: `~/storage/external-1` (if present)

## Package Management

Use `pkg` (wrapper around apt):

```
pkg update && pkg upgrade    # always do this first
pkg install python git nodejs rust golang   # install anything
pkg search <name>            # find packages
pkg list-installed           # what's installed
pkg uninstall <name>         # remove
```

Available packages include: python, nodejs, rust, golang, ruby, php, clang, cmake,
openssh, rsync, wget, curl, ffmpeg, imagemagick, neovim, tmux, htop, nmap, and 1000+ more.

## Storage Access

Android restricts file access. Run `termux-setup-storage` ONCE to create symlinks:

```
termux-setup-storage
```

This creates ~/storage/ with links to Downloads, DCIM, Music, etc.
Without this, you CANNOT access files outside Termux's own directory.

## Python

```
pkg install python
pip install <package>        # no sudo needed
python3 script.py
```

Python packages install to Termux's prefix. Some C-extension packages need:
```
pkg install python-numpy     # pre-built binary packages
LDFLAGS="-lm" pip install <package>   # if compilation fails
```

## Node.js

```
pkg install nodejs-lts
npm install -g <package>
```

## Full Linux Distros (proot-distro)

Run Ubuntu, Debian, Kali, Arch, etc. inside Termux:

```
pkg install proot-distro
proot-distro install ubuntu
proot-distro login ubuntu
```

Inside the distro you get full apt, systemctl (limited), etc.
Use this when a tool isn't available in Termux's own repos.

## SSH

```
pkg install openssh
sshd                          # start SSH server (port 8022)
ssh user@server               # connect to remote
ssh-keygen -t ed25519         # generate key
```

Termux SSH listens on port 8022 by default, not 22.

## Common Gotchas

1. **No root by default.** Commands like `apt`, `systemctl`, `mount` won't work as expected.
   Use `pkg` instead of `apt`. There is no systemd.

2. **No `/etc/hosts`, no `/etc/resolv.conf` editing.** DNS is handled by Android.

3. **Process killing.** Android aggressively kills background processes.
   Fix: disable battery optimisation for Termux in Android Settings.
   Also run `termux-wake-lock` to prevent sleep killing.

4. **Notification permission.** Termux needs notification permission to run in background.
   Grant it in Android Settings > Apps > Termux > Notifications.

5. **File permissions.** Termux's internal storage is only accessible to Termux.
   Use ~/storage/ symlinks to access shared Android storage.

6. **Keyboard.** Volume Down = Ctrl. Volume Up = special keys.
   Volume Down + C = Ctrl+C. Volume Down + L = Ctrl+L (clear).

7. **Sessions.** Swipe from left edge to open session drawer.
   Each session is an independent shell.

8. **$PREFIX confusion.** Termux binaries are in $PREFIX/bin, not /usr/bin.
   Most tools handle this, but scripts with hardcoded `/usr/bin/env` need:
   `termux-fix-shebang script.sh`

## Manufacturer-Specific Issues

- **Xiaomi/MIUI:** Settings > Battery > App battery saver > Termux > No restrictions
- **Samsung:** Settings > Battery > Background usage limits > Never sleeping apps > Add Termux
- **Huawei/EMUI:** Settings > Battery > App launch > Termux > Manage manually > Enable all
- **OnePlus/Oppo:** Settings > Battery > Battery optimisation > Termux > Don't optimise

## Useful One-Liners

```bash
# Device info
getprop ro.product.model            # phone model
getprop ro.build.version.release    # Android version
df -h                               # storage space
free -h                             # RAM usage
cat /proc/cpuinfo | head -5         # CPU info

# Networking
ifconfig wlan0                      # IP address
ping -c 3 google.com               # connectivity check
curl ifconfig.me                    # public IP

# File management
find ~/storage/downloads -name "*.pdf" -mtime -7   # recent PDFs
du -sh ~/storage/*                  # storage usage per folder
tar -czf backup.tar.gz ~/projects   # backup

# Process management
ps aux                              # running processes
kill %1                             # kill background job
nohup command &                     # run after terminal closes
```

## Setting Up a Dev Environment

```bash
# Full web dev setup
pkg update && pkg install python nodejs-lts git openssh

# Python project
python3 -m venv myenv && source myenv/bin/activate
pip install flask requests

# Clone and work on a repo
git clone https://github.com/user/repo ~/projects/repo
cd ~/projects/repo

# Set up git identity
git config --global user.name "Name"
git config --global user.email "email@example.com"
```
