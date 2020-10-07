#!/usr/bin/env bash

set -euo pipefail

main() {
  # pyenv virtualenv 3.7.7 notebooks_3.7.7
  # echo "notebooks_3.7.7" > .python_version

  which python
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
}

main "$@"
