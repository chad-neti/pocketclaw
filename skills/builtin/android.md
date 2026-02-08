---
name: android
version: 1.0.0
description: Android device control via Termux:API
author: pocketclaw
layer: 1
category: core
requires:
  - termux-api
tools:
  - name: termux_api
    description: "Call any Termux:API command for phone features: SMS, calls, location, battery, clipboard, camera, notifications, sensors, WiFi, torch, vibrate, TTS."
    parameters:
      command:
        type: string
        description: "The termux-* command (e.g. termux-sms-send, termux-battery-status)"
        required: true
      args:
        type: array
        description: "Command arguments"
        required: false
---

# Android Tools

Access phone features through Termux:API commands.

## Available Commands

- `termux-battery-status`  - Battery level and status
- `termux-sms-send -n NUMBER BODY`  - Send SMS
- `termux-sms-list`  - List SMS messages
- `termux-location`  - GPS coordinates
- `termux-clipboard-get` / `termux-clipboard-set`  - Clipboard
- `termux-notification-list`  - Read notifications
- `termux-camera-photo`  - Take a photo
- `termux-torch on/off`  - Flashlight
- `termux-vibrate`  - Vibrate
- `termux-tts-speak TEXT`  - Text to speech
- `termux-wifi-connectioninfo`  - WiFi info
- `termux-telephony-call NUMBER`  - Make a call
