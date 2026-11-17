# DaVinci Resolve MCP Server

A local **MCP (Model Context Protocol)** server that provides a small, explicit tool surface for controlling [DaVinci Resolve](https://www.blackmagicdesign.com/products/davinciresolve) through its official scripting API.

It connects to the already-running Resolve instance over stdio — no network listener, no external dependencies beyond the Python `mcp` package and Resolve's bundled scripting module.

## Features

### Read-only tools
- **`resolve_status`** — Resolve version, active page, current project, current timeline
- **`list_projects`** — List projects in the current project library folder
- **`list_media_pool`** — List clip names from the project's root Media Pool folder

### State-changing tools *(use only on explicit request)*
- **`set_page`** — Switch workspace page (`media`, `cut`, `edit`, `fusion`, `color`, `fairlight`, `deliver`)
- **`create_project`** — Create and activate a new project
- **`save_current_project`** — Save the active project to disk
- **`import_media`** — Import existing media files into the Media Pool
- **`create_empty_timeline`** — Create a blank timeline
- **`append_media_pool_clips`** — Append clips from the Media Pool to the current timeline

### What is NOT included
No tools for deleting projects/clips, rendering, exporting, arbitrary shell execution, or network access. The surface is intentionally minimal.

## Requirements

- **DaVinci Resolve Studio** (free or paid), open and fully started
- **External scripting** set to **Local** (Preferences → System → General)
- **Automatic scripted actions** at **Allow safe** (or higher)
- Python 3.11+ (tested with 3.14)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/davinci-resolve-mcp.git
cd davinci-resolve-mcp
```

### 2. Set up a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### 3. Configure environment variables

The server needs to find Resolve's scripting modules. Set these before starting:

```bash
export RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
export RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
export PYTHONPATH="$RESOLVE_SCRIPT_API/Modules:.:$PYTHONPATH"
```

### 4. Run

```bash
python -m resolve_mcp.server
```

The server communicates over stdio using the MCP protocol.

## Integration with MCP Clients

### Using with a standalone MCP host

Configure your MCP host (e.g. Claude Desktop, Cursor, or a custom host) to launch the server:

```json
{
  "mcpServers": {
    "davinci-resolve": {
      "command": "python",
      "args": ["-m", "resolve_mcp.server"],
      "env": {
        "RESOLVE_SCRIPT_API": "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting",
        "RESOLVE_SCRIPT_LIB": "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so",
        "PYTHONPATH": "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules:."
      }
    }
  }
}
```

### Using with DaVinci Resolve Native MCP

DaVinci Resolve 21+ ships with its own native MCP server at:
```
/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Applications/ResolveMCP
```

This project's Python MCP server is a complementary layer that adds higher-level tools (project creation, media import, timeline manipulation) on top of Resolve's scripting API.

## API Documentation

Complete API stubs and documentation are included in this repository:

- **`api-stubs/`** — Python type stubs (`.pyi`) for the scripting API
  - `DaVinciResolveScript.pyi` — Main API: projects, timelines, media pool, render jobs
  - `fusion_api.pyi` — Fusion compositing API
  - `ui_api.pyi` — Fusion UI Manager API
- **`docs/`** — Official Blackmagic Design documentation
  - `README.md` — Scripting API guide
  - `DCTLReadme.txt` — DCTL (DaVinci Color Transform Language) reference

## Running Tests

```bash
# Unit tests (no Resolve instance required)
python -m unittest discover -s tests -v

# Smoke test (requires Resolve running + environment variables set)
python tests/smoke_test_mcp.py
```

## Architecture

```
┌──────────────┐     stdio (MCP)      ┌──────────────────┐
│  MCP Host    │ ◄──────────────────► │  MCP Server      │
│  (Claude,    │                      │  (Python)        │
│   Cursor,    │                      │                  │
│   custom)    │                      │  resolve_mcp/    │
└──────┬───────┘                      │    server.py     │
       │                              │    core.py       │
       │  Python COM                   └────────┬─────────┘
       ▼                                       ▼
┌─────────────────────────────────────────────────────────┐
│               DaVinci Resolve (running)                  │
│                                                          │
│  DaVinciResolveScript module ─► Scripting API           │
│  (COM/ActiveX via pythoncom)                             │
└─────────────────────────────────────────────────────────┘
```

The server uses Resolve's Python scripting module which is built on COM/ActiveX. No TCP sockets or network protocols are involved.

## License

This MCP server implementation is MIT licensed. The Blackmagic Design API stubs and documentation included in `api-stubs/` and `docs/` are subject to Blackmagic Design's own licensing terms.

## Contributing

Contributions are welcome. Please:

1. Keep the tool surface minimal and explicit
2. Add tests for any new logic in `core.py`
3. Update the README if you add new tools
