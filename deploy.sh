#!/usr/bin/env sh
# Take a clean clone to a running application in one command.
#
# This is the script referenced by the Configuration Management Report (A2 Part B,
# section 4.2) and by Definition of Done criterion 5 (clean-checkout verification,
# WBS 5.3). It performs no step that a volunteer could not perform by following
# the README, and it needs nothing that is not already on a machine with Python
# and Git installed. The $0 budget constraint means no dependency is downloaded
# beyond the pinned development and test tooling.
#
# Usage:
#     sh deploy.sh
#
# Exit status is 0 only if the application starts and the test suite passes.

set -eu

PYTHON="${PYTHON:-python3}"
VENV_DIR=".venv"

say() { printf '%s\n' "==> $*"; }
die() { printf '%s\n' "ERROR: $*" >&2; exit 1; }

# --- 1. Check the prerequisite --------------------------------------------------
command -v "$PYTHON" >/dev/null 2>&1 || \
    command -v python >/dev/null 2>&1 || \
    die "Python 3.11 or newer is required but was not found on PATH."

[ "$PYTHON" = "python3" ] && command -v python3 >/dev/null 2>&1 || PYTHON="python"

"$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' || \
    die "Python 3.11 or newer is required; found $("$PYTHON" --version 2>&1)."

"$PYTHON" -c 'import venv' >/dev/null 2>&1 || \
    die "The venv module is unavailable. On Debian/Ubuntu install python3-venv."

say "Using $("$PYTHON" --version 2>&1)"

# --- 2. Create the virtual environment -----------------------------------------
if [ ! -d "$VENV_DIR" ]; then
    say "Creating virtual environment in $VENV_DIR"
    "$PYTHON" -m venv "$VENV_DIR"
else
    say "Reusing the existing virtual environment in $VENV_DIR"
fi

if [ -x "$VENV_DIR/bin/python" ]; then
    VENV_PY="$VENV_DIR/bin/python"        # POSIX
elif [ -x "$VENV_DIR/Scripts/python.exe" ]; then
    VENV_PY="$VENV_DIR/Scripts/python.exe"  # Windows (Git Bash / MSYS)
else
    die "Could not find a Python interpreter inside $VENV_DIR."
fi

# --- 3. Install the pinned tooling ---------------------------------------------
say "Installing development and test tooling (no runtime dependencies)"
"$VENV_PY" -m pip install --quiet --upgrade pip
"$VENV_PY" -m pip install --quiet -r requirements.txt

say "Installing the package in editable mode"
"$VENV_PY" -m pip install --quiet -e .

# --- 4. Create config.env from the template if it is absent --------------------
if [ ! -f config.env ]; then
    say "Creating config.env from config.env.template"
    cp config.env.template config.env
else
    say "Keeping the existing config.env (never overwritten)"
fi

# --- 5. Smoke check -------------------------------------------------------------
say "Smoke check: python -m warrigal --version"
"$VENV_PY" -m warrigal --version

say "Running the test suite"
"$VENV_PY" -m pytest -q

say "Done. Activate the environment with:"
printf '      POSIX   : . %s/bin/activate\n' "$VENV_DIR"
printf '      Windows : %s\\Scripts\\activate\n' "$VENV_DIR"
