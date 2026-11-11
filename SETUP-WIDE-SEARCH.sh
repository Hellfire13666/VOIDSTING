#!/usr/bin/env bash
# EXPLICIT OPT-IN only. Never run by default VOIDSTING launcher.
set -eu
HERE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
printf '\n  ☣ VOIDSTING // OPTIONAL WIDE SEARCH SETUP\n'
printf '  Installs Maigret 0.6.6 ONLY inside this package folder.\n'
printf '  No system packages, sudo, browser, or global pip changes.\n\n'
python3 -m venv "$HERE/.wide-venv" || { printf '  ERROR: Python venv unavailable. No system settings changed.\n' >&2; exit 1; }
"$HERE/.wide-venv/bin/python" -m pip install --disable-pip-version-check 'maigret==0.6.6'
printf '\n  ✓ Optional 120-site wide discovery is installed in this folder.\n'
printf '  Launch VOIDSTING normally and use existing [3] PUBLIC DIRECTORY + WIDE.\n'
