"""Apply EXIF orientation to image pixels."""

import argparse
from pathlib import Path

import pluggy

from photostack.imaging import orient_images

hookimpl = pluggy.HookimplMarker('photostack')


@hookimpl
def photostack_addoption(parser, parsers, pluginmanager):
    sub = parsers['command'].add_parser(
        'orient',
        help='apply EXIF orientation and write corrected copies',
        parents=[parsers['shared']],
    )
    sub.add_argument('inputs', nargs='+', type=Path, help='oriented image inputs')
    sub.add_argument(
        '--output-dir',
        '-d',
        required=True,
        type=Path,
        help='directory for corrected copies',
    )
    sub.set_defaults(func=run)


def run(ns: argparse.Namespace) -> None:
    for output in orient_images(
        ns.inputs,
        ns.output_dir,
        overwrite=ns.overwrite,
    ):
        print(output)
