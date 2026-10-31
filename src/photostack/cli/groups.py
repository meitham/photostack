"""Group captures by time gaps to guide manual sequence review."""

import argparse
import json
from pathlib import Path

import pluggy

from photostack.imaging import write_groups

hookimpl = pluggy.HookimplMarker('photostack')


@hookimpl
def photostack_addoption(parser, parsers, pluginmanager):
    sub = parsers['command'].add_parser(
        'groups',
        help='group captures by EXIF time gaps for manual review',
        parents=[parsers['shared']],
    )
    sub.add_argument('inputs', nargs='+', type=Path)
    sub.add_argument(
        '--gap-seconds',
        type=float,
        default=60,
        help='start a new group after this capture-time gap (default: 60)',
    )
    sub.add_argument(
        '--output',
        '-o',
        type=Path,
        help='write JSON to a file instead of stdout',
    )
    sub.set_defaults(func=run)


def run(ns: argparse.Namespace) -> None:
    result = write_groups(
        ns.inputs,
        ns.output,
        gap_seconds=ns.gap_seconds,
        overwrite=ns.overwrite,
    )
    if ns.output is None:
        print(result, end='')
    else:
        print(result)
