#!/usr/bin/env python3
"""Install this repository into an Agent's explicitly selected Skill directory."""
import argparse
import shutil
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target',required=True,help='Existing or new parent directory used by the target Agent for Skills')
    args=parser.parse_args()
    source=Path(__file__).resolve().parents[1]
    if not (source/'SKILL.md').is_file():raise SystemExit('SKILL.md not found beside installer')
    parent=Path(args.target).expanduser().resolve();destination=parent/'wby-video-subtitles'
    if source==destination or source in destination.parents:raise SystemExit('Target must be outside this repository')
    if destination.exists():raise SystemExit(f'Target exists; update it with its original Git remote instead: {destination}')
    parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(source,destination,ignore=shutil.ignore_patterns('.git','__pycache__','*.pyc','.DS_Store','jobs'))
    print(destination)


if __name__=='__main__':main()
