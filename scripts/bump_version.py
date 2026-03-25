#!/usr/bin/env python3
"""Increment project semantic version and sync related files."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from versioning import bump_version


def main() -> int:
    parser = argparse.ArgumentParser(description='Bump semantic version and sync files')
    parser.add_argument('--part', choices=['major', 'minor', 'patch'], default='patch')
    parser.add_argument('--quiet', action='store_true')
    args = parser.parse_args()

    repo_root = REPO_ROOT
    version_file = repo_root / 'VERSION'
    config_file = repo_root / 'config.json'

    if not version_file.exists():
        raise FileNotFoundError(f"VERSION file not found: {version_file}")

    current_version = version_file.read_text(encoding='utf-8').strip()
    next_version = bump_version(current_version, args.part)
    version_file.write_text(next_version + '\n', encoding='utf-8')

    if config_file.exists():
        config = json.loads(config_file.read_text(encoding='utf-8'))
        config['version'] = next_version
        config_file.write_text(json.dumps(config, indent=4, ensure_ascii=False) + '\n', encoding='utf-8')

    if not args.quiet:
        print(f"{current_version} -> {next_version}")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
