"""Convenient local Windows MP4 workflow; never writes native Jianying drafts."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / 'skills/yichen-jianying-edit/scripts/headless_draft.py'


def run(*args):
    subprocess.run([sys.executable, str(ENTRY), *map(str, args)], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor')
    render = sub.add_parser('render', help='Build, verify and export a new MP4 job')
    render.add_argument('--plan', type=Path, required=True)
    render.add_argument('--font', type=Path)
    render.add_argument('--crf', type=int, default=18)
    args = parser.parse_args()
    if args.command == 'doctor':
        run('doctor')
        return
    if os.name != 'nt':
        parser.error('This convenience entrypoint is for Windows; use the documented platform entrypoint elsewhere.')
    plan = args.plan.expanduser().resolve(strict=True)
    font = args.font
    if font is None:
        font = next((Path(value) for value in (
            r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\simhei.ttf')
                     if Path(value).is_file()), None)
    job = ROOT / 'work' / ('windows-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid4().hex[:6])
    run('build', '--plan', plan, '--out', job / 'build')
    run('verify-build', '--build', job / 'build')
    options = ['export', '--backend', 'windows-ffmpeg', '--build', job / 'build',
               '--out', job / 'export', '--crf', args.crf]
    if font is not None:
        options += ['--font', font.expanduser().resolve(strict=True)]
    run(*options)
    print('MP4: ' + str(job / 'export/render.mp4'))
    print('Evidence: ' + str(job / 'export/result.json'))


if __name__ == '__main__':
    main()
