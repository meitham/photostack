"""Create a labeled contact sheet for manual review."""

import argparse
from pathlib import Path

import pluggy

from photostack.imaging import make_contact_sheet

hookimpl = pluggy.HookimplMarker('photostack')


@hookimpl
def photostack_addoption(parser, parsers, pluginmanager):
    sub = parsers['command'].add_parser(
        'sheet',
        help='make a labeled contact sheet',
        parents=[parsers['shared']],
    )
    sub.add_argument('inputs', nargs='+', type=Path)
    sub.add_argument('--output', '-o', required=True, type=Path)
    sub.add_argument('--columns', type=int, default=4)
    sub.add_argument('--cell-size', default='360x520')
    sub.add_argument('--font', default='DejaVu-Sans')
    sub.set_defaults(func=run)


def run(ns: argparse.Namespace) -> None:
    print(
        make_contact_sheet(
            ns.inputs,
            ns.output,
            columns=ns.columns,
            cell_size=ns.cell_size,
            font=ns.font,
            overwrite=ns.overwrite,
        )
    )
