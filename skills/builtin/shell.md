---
name: shell
version: 1.0.0
description: Execute shell commands, manage files, and run code
author: pocketclaw
layer: 1
category: core
tools:
  - name: run_shell
    description: "Execute a shell command in Termux. Returns stdout, stderr, and exit code."
    parameters:
      command:
        type: string
        description: "The shell command to execute"
        required: true
      timeout:
        type: integer
        description: "Max seconds to wait (default 30)"
        required: false
      working_dir:
        type: string
        description: "Working directory"
        required: false
  - name: run_python
    description: "Execute Python code and return output."
    parameters:
      code:
        type: string
        description: "Python code to execute"
        required: true
      timeout:
        type: integer
        description: "Max seconds (default 30)"
        required: false
  - name: read_file
    description: "Read a file's contents."
    parameters:
      path:
        type: string
        description: "File path"
        required: true
      max_lines:
        type: integer
        description: "Max lines to return"
        required: false
  - name: write_file
    description: "Create or overwrite a file."
    parameters:
      path:
        type: string
        description: "File path"
        required: true
      content:
        type: string
        description: "File contents"
        required: true
  - name: edit_file
    description: "Replace exact text in a file. old_str must appear exactly once."
    parameters:
      path:
        type: string
        description: "File path"
        required: true
      old_str:
        type: string
        description: "Text to find (must be unique)"
        required: true
      new_str:
        type: string
        description: "Replacement text"
        required: true
  - name: list_directory
    description: "List files and directories at a path."
    parameters:
      path:
        type: string
        description: "Directory path"
        required: true
      recursive:
        type: boolean
        description: "List recursively (default false)"
        required: false
  - name: http_request
    description: "Make an HTTP request to any URL."
    parameters:
      method:
        type: string
        description: "GET, POST, PUT, DELETE, PATCH"
        required: true
      url:
        type: string
        description: "The URL"
        required: true
      headers:
        type: object
        description: "Request headers"
        required: false
      body:
        type: string
        description: "Request body"
        required: false
      timeout:
        type: integer
        description: "Max seconds (default 15)"
        required: false
---

# Shell & File Tools

Core tools for executing commands, managing files, and making HTTP requests.
These are the primary Layer 1 tools  - prefer these over screen interaction whenever possible.
