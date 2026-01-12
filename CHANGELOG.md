# CHANGELOG


## v1.0.0 (2026-01-12)

### Build System

- Autoenable python venv
  ([`3f167ed`](https://github.com/aareman/superreload/commit/3f167ed45f9767c91a2dccb29128a2d5dcd3037a))

### Features

- Migrate CLI from argparse to Typer
  ([`5aa1d3f`](https://github.com/aareman/superreload/commit/5aa1d3f7e5d92b0daf2a421192b10f74b7272817))

- Replace argparse with Typer for modern CLI experience - Add styled Rich output with colored
  [superreload] prefix - Change version from subcommand to --version/-V flag - Add shell completion
  support (--install-completion) - Mark django command as deprecated in help - Add 12 CLI tests
  using typer.testing.CliRunner

BREAKING CHANGE: 'superreload version' replaced by 'superreload --version'

### BREAKING CHANGES

- 'superreload version' replaced by 'superreload --version'


## v0.3.1 (2026-01-12)

### Bug Fixes

- Import module before reload in logging test
  ([`8fe8471`](https://github.com/aareman/superreload/commit/8fe84711e187f50ceeb916b1970f4f13a4810d62))

The test was expecting 'Reloading module' log but the module wasn't loaded yet, so it took the
  'importing fresh' path instead.

### Chores

- **release**: 0.3.1
  ([`81f96a6`](https://github.com/aareman/superreload/commit/81f96a6185b9b195756daa728b103171821a3639))


## v0.3.0 (2026-01-12)

### Chores

- **release**: 0.3.0
  ([`c0909ea`](https://github.com/aareman/superreload/commit/c0909ea67df4e930d39072fcce5a5b022467a35b))

### Features

- Add --debug flag and verbose mode to Django management command
  ([`99be65a`](https://github.com/aareman/superreload/commit/99be65ad94b81160d3c97a9f6c34bc1eb096b7b0))

- Add --debug flag (equivalent to --verbosity 3) to superreload command - Integrate with Django's
  built-in --verbosity option (0-3) - Configure Python logging based on verbosity level - Print
  verbose config at startup with --verbosity >= 2: - Watch paths, patterns, ignore patterns - Force
  polling status and poll delay - Django apps detected - Add debug logging throughout reload
  operations: - Module path resolution - Module reload attempts and results - Dependency chain
  computation - Django cache clearing (URL, template, app registry) - Add tests for verbosity
  functionality

- Auto-select available port for WebSocket server
  ([`e7cbb92`](https://github.com/aareman/superreload/commit/e7cbb92d05e0c6bdb5d63e80f9fd82fac36a2e8c))

When the default port 9877 is in use, automatically find and use the next available port. Adds
  is_port_available() and find_available_port() utilities. WebSocketServer.start() now returns the
  actual port used.


## v0.2.0 (2026-01-12)

### Bug Fixes

- Skip __main__ module in reload dependency scan
  ([`1c1283d`](https://github.com/aareman/superreload/commit/1c1283dc0534ecacc7629ef88b4a0c68cb99d5a9))

- Use jurigged registry.prepare() for proper hot reload tracking
  ([`049e0db`](https://github.com/aareman/superreload/commit/049e0db61abbaf339046fc2cf239da85085f7ee9))

### Chores

- Add jurigged as core dependency
  ([`2e6d0d3`](https://github.com/aareman/superreload/commit/2e6d0d35c465f981db42dc7312f26c7ef4cdde6a))

- **release**: 0.2.0
  ([`512a07b`](https://github.com/aareman/superreload/commit/512a07b8c45e5230acd465d4150cae7ce4432c52))

### Continuous Integration

- Skip existing packages on PyPI publish
  ([`12ebe9a`](https://github.com/aareman/superreload/commit/12ebe9ac4d4a98fda8a92710900fcf2da32ef9da))

### Documentation

- Add CLI documentation and update README
  ([`68ae43d`](https://github.com/aareman/superreload/commit/68ae43dc1ec3230aacd061d3e423f587d8087790))

### Features

- Add CLI for running scripts with hot reload
  ([`858332e`](https://github.com/aareman/superreload/commit/858332eec570d45e1264b960806deae925cded10))

Uses jurigged for surgical code patching by default. Supports --simple flag for re-execute mode and
  --full-reload for process restart. Includes --watch, --gitignore, and --ignore options.

- Add gitignore parser for file filtering
  ([`39d4903`](https://github.com/aareman/superreload/commit/39d4903879d6b8724a1d05053cbb276198d1bcf3))


## v0.1.0 (2026-01-12)

### Bug Fixes

- Clarify console reload shortcut requires Enter key
  ([`356021c`](https://github.com/aareman/superreload/commit/356021c3970ac07553dcb1ff869717f30b7110c5))

- Clear template cache on HTML file changes for proper reload
  ([`6a96d4e`](https://github.com/aareman/superreload/commit/6a96d4eec03ea551e0bbeeaff451826d8d827dbb))

- Correct reload order and dedupe file changes
  ([`9dbe3d1`](https://github.com/aareman/superreload/commit/9dbe3d1157e9fcd35590b5faa131b3828c564e7d))

- Reload changed modules before dependents so imports get fresh references - Deduplicate file paths
  from watchfiles (reports same file twice sometimes) - Remove _ensure_mtime_changed() which caused
  infinite reload loops - Use glob-based bytecode cache clearing for pytest compatibility - Add
  loader cache clearing for more reliable reloads

- Css hot reload closure bug and enable static dir watching
  ([`4fc8497`](https://github.com/aareman/superreload/commit/4fc84976d7694ff81a92672f5944039cae4336b6))

- Inject reload script into error pages for recovery
  ([`cd59f57`](https://github.com/aareman/superreload/commit/cd59f5750b209ff6a415f6c3671e82f1dcd88bf0))

- Only bump mtime when file modified within last second
  ([`15d1719`](https://github.com/aareman/superreload/commit/15d171949acb39bf177d9db83065efac5bc37b42))

Previously, mtime was bumped unconditionally which caused editors to show 'file changed on disk'
  warnings. Now we only bump mtime when the file was modified within the last second, which is only
  needed for Python's second-level mtime granularity edge case in tests.

- Reload root URLconf to pick up new view references
  ([`b71ee84`](https://github.com/aareman/superreload/commit/b71ee84045929ed9faa8b3d64e3a3d054d8ab772))

- Resolve mypy type errors for CI compatibility
  ([`033b82e`](https://github.com/aareman/superreload/commit/033b82e76c50a2eeacc2b59dbab3045b213de802))

- Rtd build by creating output directory before copy
  ([`a338619`](https://github.com/aareman/superreload/commit/a338619ab02d3e2e90436ca0841bdb398bed8c25))

- Set correct baseUrl for Read the Docs builds
  ([`d115638`](https://github.com/aareman/superreload/commit/d1156381e285863a6ec9b8a4b722557fed67ea2c))

- Use standard python build in semantic-release
  ([`a2264ae`](https://github.com/aareman/superreload/commit/a2264aedf167f30f3af35ea7bebb7e486efd8ddc))

### Chores

- Add debug output for file change detection
  ([`6d4aa65`](https://github.com/aareman/superreload/commit/6d4aa6592aa615e35ad5829e987874bdc2c48c00))

- Add more debug logging for file change handling
  ([`9ebd83e`](https://github.com/aareman/superreload/commit/9ebd83ea9051bafc7f6937ac0302ccf2ed65606c))

- Remove GitHub Pages workflow, use Read the Docs only
  ([`1aa5354`](https://github.com/aareman/superreload/commit/1aa5354bcd2b7d9a9e143ef7104acadae604cc13))

- **release**: 0.1.0
  ([`ceb255e`](https://github.com/aareman/superreload/commit/ceb255ec66ec8cacd5fc2f6fc731ef1191ac2020))

### Continuous Integration

- Add GitHub Actions for testing and linting on Python 3.9-3.13
  ([`a76705d`](https://github.com/aareman/superreload/commit/a76705d984038fb767e4662384903422522e0e4b))

- Add semantic release workflow with PyPI publishing
  ([`e6cf9c5`](https://github.com/aareman/superreload/commit/e6cf9c5e83f5f6cbf3e06347f605a05aeffeebdc))

### Documentation

- Add --ws-path documentation
  ([`12779ce`](https://github.com/aareman/superreload/commit/12779ce7ec62b319596ea7c618f223565c9cb121))

- Add AGENTS.md project knowledge base
  ([`94b2e61`](https://github.com/aareman/superreload/commit/94b2e6179be67402b00a85223be73705e610c880))

- Add conventional commit guidelines to CONTRIBUTING.md
  ([`ea4fe31`](https://github.com/aareman/superreload/commit/ea4fe310dc46bd1263220fe79f254d8879e1d05c))

- Add Docker setup, --force-polling, and hot reload limitations
  ([`2dcbc5d`](https://github.com/aareman/superreload/commit/2dcbc5dd823d4eed6a5d1f200455a2896ebdc3be))

- Add Docusaurus documentation site, update README, add CONTRIBUTING.md
  ([`2a4df27`](https://github.com/aareman/superreload/commit/2a4df278c931e7c57c5e6417bbbb112c788ac2d2))

- Add Read the Docs configuration
  ([`5e5077d`](https://github.com/aareman/superreload/commit/5e5077d841d56baf6bcaf719ad8bf7f1629d1aa4))

- Update CLI args and add keyboard shortcuts documentation
  ([`818657e`](https://github.com/aareman/superreload/commit/818657ede5e6c3c9f3f385b0d5ec9dab8ffc684f))

### Features

- Add --force-polling option for Docker file watching
  ([`20236a7`](https://github.com/aareman/superreload/commit/20236a7c89ce34da7ce6f3339501a774aee02a1a))

- Add --ws-path option for configurable WebSocket URL path
  ([`db95cf8`](https://github.com/aareman/superreload/commit/db95cf8b428a027913cca5961cdff94d9ab4a20d))

- Add configurable WebSocket host and secure (wss) settings
  ([`a6e99ea`](https://github.com/aareman/superreload/commit/a6e99ea81e25873dc8757b93b0dff15e95fb1aa5))

- Add error overlay with stack traces and local variables
  ([`014094e`](https://github.com/aareman/superreload/commit/014094efed934160a910b8912db60c161bf23c5a))

Show Python errors in browser with beautiful dark-themed overlay: - Full stack trace with file
  locations - Local variables for each stack frame - Source code context with error line highlighted
  - Dismiss with ESC or close button

- Add keyboard shortcuts for manual reload (Ctrl+Shift+R in browser, 'r' in console)
  ([`8439809`](https://github.com/aareman/superreload/commit/84398095b6970bda18f7a423335844d4bdbf0fa2))

- Clear Django app registry caches after reload
  ([`a5691dc`](https://github.com/aareman/superreload/commit/a5691dca1fcd6cb5a9252948cee81eb6fcf0b928))

- Css/js hot reload without full page refresh
  ([`b87c9c4`](https://github.com/aareman/superreload/commit/b87c9c4f6f1002cb79f47f24b0d9b7960a487966))

CSS changes now update stylesheets in-place without refreshing. JS changes still trigger full reload
  for safety (state management).

- Initial superreload implementation
  ([`eb08208`](https://github.com/aareman/superreload/commit/eb082087533df4fbd80198f6209c3fe35bfe6d7a))

Complete implementation of superreload, a hot reload tool for Django that watches Python files,
  reloads modules in-place without server restart, and auto-refreshes the browser via WebSocket.

Core features: - File watcher using watchfiles for efficient filesystem monitoring - Module reloader
  with importlib.reload and mtime bump for cache bypass - WebSocket server for browser notification
  - Django middleware for injecting JS client into HTML responses - Django framework adapter with
  URL/template cache clearing - Reload cooldown mechanism to prevent infinite reload loops

Fixes applied: - Force source reload by bumping mtime (Python uses second-level granularity) - Clear
  bytecode cache to prevent stale .pyc issues - Update websockets import from deprecated
  WebSocketServerProtocol to ServerConnection

- Trigger first release
  ([`a66d215`](https://github.com/aareman/superreload/commit/a66d215fd0cd9ef3ff29937cbbb43689a96a5449))

### Refactoring

- Clean up debug logging, keep useful status messages
  ([`c24d67c`](https://github.com/aareman/superreload/commit/c24d67c462099eddde393285d7caef0427b294a6))

- Rename management command args to --ws-host, --ws-port, --no-reload
  ([`68f9ba0`](https://github.com/aareman/superreload/commit/68f9ba06948a90e732db3e41a177fd3bd36c0a4c))

### Testing

- Add Django integration tests for framework, middleware, and reload server
  ([`7f0577e`](https://github.com/aareman/superreload/commit/7f0577e2c6a05788331c7bdc6c42967829bfafe7))
