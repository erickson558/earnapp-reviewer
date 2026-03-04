#!/usr/bin/env python3
"""Increment project semantic version and sync related files."""

import argparse
import json
from pathlib import Path


def parse_version(raw: str) -> tuple[int, int, int]:
    parts = raw.strip().split('.')
    if len(parts) != 3:
        raise ValueError(f"Invalid version '{raw}'. Expected MAJOR.MINOR.PATCH")

    major, minor, patch = (int(part) for part in parts)
    return major, minor, patch


def format_version(major: int, minor: int, patch: int) -> str:
    return f"{major}.{minor}.{patch}"


def bump(current: str, part: str) -> str:
    major, minor, patch = parse_version(current)

    if part == 'major':
        major += 1
        minor = 0
        patch = 0
    elif part == 'minor':
        minor += 1
        patch = 0
    else:
        patch += 1

    return format_version(major, minor, patch)


def main() -> int:
    parser = argparse.ArgumentParser(description='Bump semantic version and sync files')
    parser.add_argument('--part', choices=['major', 'minor', 'patch'], default='patch')
    parser.add_argument('--quiet', action='store_true')
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    version_file = repo_root / 'VERSION'
    config_file = repo_root / 'config.json'

    if not version_file.exists():
        raise FileNotFoundError(f"VERSION file not found: {version_file}")

    current_version = version_file.read_text(encoding='utf-8').strip()
    next_version = bump(current_version, args.part)
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
