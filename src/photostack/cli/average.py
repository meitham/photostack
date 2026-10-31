"""Average a selected set of views with equal weights."""

import argparse
from pathlib import Path

import pluggy

from photostack.imaging import average_images

hookimpl = pluggy.HookimplMarker('photostack')


@hookimpl
def photostack_addoption(parser, parsers, pluginmanager):
    sub = parsers['command'].add_parser(
        'average',
        help='average a set of images with equal weights',
        parents=[parsers['shared']],
    )
    sub.add_argument('inputs', nargs='+', type=Path)
    sub.add_argument('--output', '-o', required=True, type=Path)
    sub.set_defaults(func=run)


def run(ns: argparse.Namespace) -> None:
    print(
        average_images(
            ns.inputs,
            ns.output,
            overwrite=ns.overwrite,
        )
    )
