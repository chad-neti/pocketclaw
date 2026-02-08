---
name: system
version: 1.0.0
description: Screen reading and interaction for Android apps
author: pocketclaw
layer: 2
category: core
tools:
  - name: screen_read
    description: "Read current screen UI elements as structured data. Returns all visible elements with text, type, bounds, clickable status. Use BEFORE screen_tap to know what's on screen."
    parameters: {}
  - name: screen_tap_element
    description: "Tap a UI element by its text or description. Preferred over coordinates."
    parameters:
      text:
        type: string
        description: "Text or content-description of the element"
        required: true
      element_type:
        type: string
        description: "Filter: button, text, input, etc."
        required: false
      index:
        type: integer
        description: "Which match if multiple (0-indexed)"
        required: false
  - name: screen_type_text
    description: "Type text into the focused input field."
    parameters:
      text:
        type: string
        description: "Text to type"
        required: true
      clear_first:
        type: boolean
        description: "Clear field first (default false)"
        required: false
  - name: screen_scroll
    description: "Scroll the screen in a direction."
    parameters:
      direction:
        type: string
        description: "up, down, left, right"
        required: true
      amount:
        type: integer
        description: "Pixels to scroll (default 500)"
        required: false
  - name: screenshot
    description: "Take a screenshot. ONLY use when screen_read can't provide enough info. Slow."
    parameters:
      scale:
        type: number
        description: "Scale factor 0.1-1.0 (default 0.5)"
        required: false
  - name: screen_tap_coordinates
    description: "Tap at x,y coordinates. Use after screenshot. Prefer screen_tap_element."
    parameters:
      x:
        type: integer
        description: "X coordinate"
        required: true
      y:
        type: integer
        description: "Y coordinate"
        required: true
---

# Screen Interaction Tools

For controlling Android apps that don't have APIs.

## Usage Pattern

1. `screen_read` — see what's on screen
2. `screen_tap_element` — interact with elements by name
3. `screenshot` — only if screen_read can't parse the UI

Layer 2 (accessibility) is always faster than Layer 3 (screenshots).
