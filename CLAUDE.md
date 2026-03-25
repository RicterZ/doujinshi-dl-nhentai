# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

`doujinshi-dl-nhentai` is the nhentai plugin for `doujinshi-dl`. It registers itself via the `doujinshi_dl.plugins` entry point group and is auto-discovered at runtime by the main package. PyPI distribution name: `doujinshi-dl-nhentai`, Python package name: `doujinshi_dl_nhentai`.

## Development Setup

```bash
# Install both packages in editable mode (plugin depends on main package)
pip install -e /path/to/nhentai        # main package first
pip install -e /path/to/doujinshi-dl-nhentai

# Or with Poetry
poetry install
```

## Entry Point Registration

```toml
[tool.poetry.plugins."doujinshi_dl.plugins"]
nhentai = "doujinshi_dl_nhentai:plugin"
```

The entry point points to the module-level `plugin` instance in `__init__.py`, not the class.

## Architecture

| Module | Role |
|--------|------|
| `__init__.py` | Exposes the singleton `plugin = Plugin()` consumed by the entry point |
| `plugin.py` | `Plugin(BasePlugin)` — factory for parser/model/serializer; implements `configure()`, `check_auth()`, `print_results()` |
| `adapters.py` | `ParserAdapter`, `DoujinshiAdapter`, `SerializerAdapter` — bridge between core interfaces and nhentai internals |
| `parser.py` | HTTP scraping: `doujinshi_parser()`, `search_parser()`, `legacy_search_parser()`, `favorites_parser()`, `print_doujinshi()` |
| `model.py` | `Doujinshi` model — holds metadata, builds download queue, formats folder names |
| `serializer.py` | Writes `metadata.json`, `ComicInfo.xml`, `info.txt`; `set_js_database()` for main viewer |
| `http.py` | `request()`, `async_request()`, `get_headers()`, `check_cookie()` — all HTTP calls inject auth headers from `CONFIG` |
| `constant.py` | All URLs, paths, and config defaults |

### Plugin Interface Implemented

```python
plugin.configure(args)      # writes args → constant.CONFIG; registers history_path / base_url / plugin_config in core_config
plugin.check_auth()         # calls check_cookie()
plugin.print_results(list)  # calls print_doujinshi()
plugin.create_parser()      # → ParserAdapter
plugin.create_model(meta, name_format)   # → DoujinshiAdapter
plugin.create_serializer()  # → SerializerAdapter
serializer.finalize(dir)    # calls set_js_database()
```

## Key Constants (`constant.py`)

```python
NHENTAI_HOME        # config/history directory (~/.doujinshi-dl or ~/.nhentai legacy)
NHENTAI_HISTORY     # SQLite history DB path
NHENTAI_CONFIG_FILE # JSON config file path

# Generic aliases for plugin-agnostic callers in the main package
PLUGIN_HOME         = NHENTAI_HOME
PLUGIN_HISTORY      = NHENTAI_HISTORY
PLUGIN_CONFIG_FILE  = NHENTAI_CONFIG_FILE

CONFIG              # dict: cookie, proxy, useragent, language, template, max_filename
BASE_URL            # from DOUJINSHI_DL_URL env var
```

## Tests

Tests are integration tests that make real HTTP requests.

```bash
export DDL_COOKIE="<cookie>"
export DDL_UA="<user-agent>"
export DOUJINSHI_DL_URL="<mirror-url>"

python -m unittest discover tests/

# Single file
python -m unittest tests.test_parser
python -m unittest tests.test_login
python -m unittest tests.test_download
```
