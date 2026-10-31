"""Apply an ImageMagick gamma curve."""

import argparse
from pathlib import Path

import pluggy

from photostack.imaging import tone_image

hookimpl = pluggy.HookimplMarker('photostack')


@hookimpl
def photostack_addoption(parser, parsers, pluginmanager):
    sub = parsers['command'].add_parser(
        'tone',
        help='apply a gamma curve to an image',
        parents=[parsers['shared']],
    )
    sub.add_argument('input', type=Path)
    sub.add_argument('--gamma', required=True, type=float)
    sub.add_argument('--output', '-o', required=True, type=Path)
    sub.set_defaults(func=run)


def run(ns: argparse.Namespace) -> None:
    print(
        tone_image(
            ns.input,
            ns.output,
            gamma=ns.gamma,
            overwrite=ns.overwrite,
        )
    )
