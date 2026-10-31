"""Extract an embedded camera JPEG preview from RAW files."""

import argparse
from pathlib import Path

import pluggy

from photostack.imaging import extract_previews

hookimpl = pluggy.HookimplMarker('photostack')


@hookimpl
def photostack_addoption(parser, parsers, pluginmanager):
    sub = parsers['command'].add_parser(
        'preview',
        help='extract embedded JPEG previews from RAW files',
        parents=[parsers['shared']],
    )
    sub.add_argument('inputs', nargs='+', type=Path, help='RAW input files')
    sub.add_argument(
        '--output-dir',
        '-d',
        required=True,
        type=Path,
        help='directory for extracted JPEG previews',
    )
    sub.set_defaults(func=run)


def run(ns: argparse.Namespace) -> None:
    for output in extract_previews(
        ns.inputs,
        ns.output_dir,
        overwrite=ns.overwrite,
    ):
        print(output)
