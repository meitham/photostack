"""Build a sequential blend stack from an ordered list of images."""

import argparse
from pathlib import Path

import pluggy

from photostack.imaging import stack_images

hookimpl = pluggy.HookimplMarker('photostack')

_MODES = ('normal', 'multiply', 'screen', 'overlay', 'softlight')


@hookimpl
def photostack_addoption(parser, parsers, pluginmanager):
    sub = parsers['command'].add_parser(
        'stack',
        help='blend an ordered series of images',
        parents=[parsers['shared']],
    )
    sub.add_argument(
        'inputs',
        nargs='+',
        type=Path,
        help='ordered images; the first is the base',
    )
    sub.add_argument('--mode', choices=_MODES, default='overlay')
    sub.add_argument(
        '--opacity',
        type=float,
        default=0.2,
        help='opacity for each added layer from 0 to 1 (default: 0.2)',
    )
    sub.add_argument('--output', '-o', required=True, type=Path)
    sub.set_defaults(func=run)


def run(ns: argparse.Namespace) -> None:
    print(
        stack_images(
            ns.inputs,
            ns.output,
            mode=ns.mode,
            opacity=ns.opacity,
            overwrite=ns.overwrite,
        )
    )
