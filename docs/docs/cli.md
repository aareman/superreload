---
sidebar_position: 3
---

# CLI Usage

superreload provides a command-line interface for running Python scripts with hot reloading.

## Running Scripts

Run any Python script with automatic hot reloading:

```bash
superreload run script.py
```

### How It Works

By default, superreload uses [jurigged](https://github.com/breuleux/jurigged) for surgical code patching:

- **Function/class changes**: Patched in-place without restart
- **Module-level changes**: May require restart depending on the change
- **State preservation**: Variables and objects are preserved across reloads

This gives you instant feedback for code changes while preserving your program's state.

## Options

### `--watch`, `-w`

Watch additional directories for changes:

```bash
superreload run script.py --watch src/ --watch lib/
```

By default, only the script's parent directory is watched.

### `--gitignore`

Use `.gitignore` patterns to exclude files:

```bash
superreload run script.py --watch . --gitignore
```

This reads `.gitignore` files from watched directories and excludes matching files.

### `--full-reload`

Always restart the script on any change (instead of hot reloading):

```bash
superreload run script.py --full-reload
```

Use this when hot reloading isn't working correctly for your use case.

### `--simple`

Use simple mode instead of jurigged. Re-executes the script on file changes:

```bash
superreload run script.py --simple
```

This is a lightweight alternative that doesn't require jurigged. Useful for:
- Scripts with complex module dependencies
- When jurigged causes issues
- Simpler debugging

### `--ignore`, `-i`

Add custom ignore patterns:

```bash
superreload run script.py --ignore "*.tmp" --ignore "*.log"
```

### Passing Arguments to Your Script

Use `--` to separate superreload options from script arguments:

```bash
superreload run server.py --watch src/ -- --port 8080 --debug
```

## Examples

### Basic Usage

```bash
# Run a script, watch only the script file's directory
superreload run app.py
```

### Watch Entire Project

```bash
# Watch the whole project, respecting .gitignore
superreload run main.py --watch . --gitignore
```

### Development Server

```bash
# Run a server with hot reloading
superreload run server.py --watch src/ --watch config/ -- --host 0.0.0.0 --port 8000
```

### Full Restart Mode

```bash
# Always restart (useful for scripts that don't support hot reload)
superreload run worker.py --watch . --full-reload
```

## Behavior Summary

| Mode | File Change Behavior | State Preservation |
|------|---------------------|-------------------|
| Default (jurigged) | Surgical code patching | Yes |
| `--simple` | Re-execute script | No |
| `--full-reload` | Full process restart | No |
