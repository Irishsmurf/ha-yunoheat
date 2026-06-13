# Contributing

Issues and pull requests are welcome. This page covers the development setup, the checks
that run, how the documentation is built, and how releases are cut.

## Project layout

```
custom_components/yunoheat/   the integration
  __init__.py                 entry setup / teardown
  config_flow.py              UI setup + reauth
  coordinator.py              6-hour polling, YunoHeatData
  entity.py                   shared base entity / device
  sensor.py                   sensor platform
  token_store.py              token persistence in the config entry
  const.py                    constants
  manifest.json               metadata + pyyunoheat pin
  strings.json                UI + entity strings
  translations/en.json        English translations
  brand/                      HACS brand assets (SVG sources + PNGs)
docs/                         MkDocs documentation (this site)
.github/workflows/            CI: lint, hassfest, HACS validate, release
```

## Development setup

The integration runs inside Home Assistant; there is no standalone app to launch. Day to
day you just need Ruff for linting:

```bash
pip install ruff
ruff check .
```

`ruff check .` is the **only** local check — there are no tests in this repository.

### Working against the API library

All API access goes through [`pyyunoheat`](https://pypi.org/project/pyyunoheat/) (import
name `yunoheat`), pinned in `manifest.json`. When changing how the integration talks to the
API, consult the library's own `API_REFERENCE.md` and source for the real client API,
models, and exceptions rather than guessing — the installed version may lag the manifest
pin.

## Coding conventions

- Follow modern Home Assistant core patterns: `runtime_data`, entity descriptions, and
  translation keys defined in `strings.json` / `translations/`.
- Translate the library's exceptions into Home Assistant's at the boundary — see the naming
  trap in [Architecture](architecture.md#the-pyyunoheat-library).
- To add a sensor, add a `YunoHeatSensorEntityDescription` to the `SENSORS` tuple in
  `sensor.py` and a matching entry under `entity.sensor` in `strings.json` /
  `translations/en.json`.

## Continuous integration

Every push and pull request runs three workflows:

| Workflow | What it checks |
| --- | --- |
| **Lint** | `ruff check .` |
| **Hassfest** | Home Assistant's manifest / structure validation |
| **Validate** | HACS repository validation |

Make sure `ruff check .` passes locally before opening a pull request.

## Branding assets

Brand assets live in `custom_components/yunoheat/brand/` (HACS requires this exact directory
name). The editable sources are SVGs — `icon.svg` (512×512), `logo.svg`, and `dark_logo.svg`
(2186×512, wordmark indigo `#363086` / white). The wordmark is Quicksand Bold outlined to
vector paths, so the SVGs have no font dependency.

The shipped PNGs follow the Home Assistant brands image spec (transparent, trimmed,
interlaced, lossless-optimized) with a normal + hDPI pair for each asset. Don't hand-edit the
PNGs — regenerate them from the SVGs. See `CLAUDE.md` in the repository root for the exact
render/trim/optimize recipe.

## Building the documentation

The docs are a [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) site:

```bash
pip install -r requirements-docs.txt
mkdocs serve     # live preview at http://127.0.0.1:8000
mkdocs build     # render the static site into site/
```

Documentation pages live in `docs/`; navigation and theming are configured in `mkdocs.yml`.

## Cutting a release

1. Bump `version` in `custom_components/yunoheat/manifest.json`.
2. Commit and push to `main`.
3. Tag and push the tag:

    ```bash
    git tag vX.Y.Z
    git push origin vX.Y.Z
    ```

   The **Release** workflow publishes the GitHub release from the tag, and HACS picks it up
   from there.
