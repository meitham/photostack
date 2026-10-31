"""Crop an image using ImageMagick geometry syntax."""

import argparse
from pathlib import Path

import pluggy

from photostack.imaging import crop_image

hookimpl = pluggy.HookimplMarker('photostack')


@hookimpl
def photostack_addoption(parser, parsers, pluginmanager):
    sub = parsers['command'].add_parser(
        'crop',
        help='crop an image (for example, 2400x4200+500+600)',
        parents=[parsers['shared']],
    )
    sub.add_argument('input', type=Path)
    sub.add_argument('--geometry', required=True)
    sub.add_argument('--output', '-o', required=True, type=Path)
    sub.set_defaults(func=run)


def run(ns: argparse.Namespace) -> None:
    print(
        crop_image(
            ns.input,
            ns.output,
            geometry=ns.geometry,
            overwrite=ns.overwrite,
        )
    )
