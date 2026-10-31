"""Blend one image layer over a base image."""

import argparse
from pathlib import Path

import pluggy

from photostack.imaging import blend_images

hookimpl = pluggy.HookimplMarker('photostack')

_MODES = ('normal', 'multiply', 'screen', 'overlay', 'softlight')


@hookimpl
def photostack_addoption(parser, parsers, pluginmanager):
    sub = parsers['command'].add_parser(
        'blend',
        help='blend one layer over a base image',
        parents=[parsers['shared']],
    )
    sub.add_argument('base', type=Path, help='base image')
    sub.add_argument('layer', type=Path, help='image layer')
    sub.add_argument('--mode', choices=_MODES, default='overlay')
    sub.add_argument(
        '--opacity',
        type=float,
        default=0.2,
        help='layer opacity from 0 to 1 (default: 0.2)',
    )
    sub.add_argument('--output', '-o', required=True, type=Path)
    sub.set_defaults(func=run)


def run(ns: argparse.Namespace) -> None:
    print(
        blend_images(
            ns.base,
            ns.layer,
            ns.output,
            mode=ns.mode,
            opacity=ns.opacity,
            overwrite=ns.overwrite,
        )
    )
