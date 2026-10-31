import argparse
import importlib
import pathlib
import pdb
import sys
import traceback

import pluggy

from photostack import hookspecs, logs
from photostack.imaging import PhotoStackError


def get_plugin_manager():
    pm = pluggy.PluginManager('photostack')
    pm.add_hookspecs(hookspecs)
    pm.load_setuptools_entrypoints('photostack')
    plugins = pathlib.Path(__file__).parent.glob('*.py')
    for plug in plugins:
        if plug.stem == '__init__':
            continue
        mod = importlib.import_module(f'photostack.cli.{plug.stem}')
        pm.register(mod)
    return pm


def attach_debugger():
    """drop to pdb (or better pdbpp) on errors"""

    def info(type, value, tb):
        if hasattr(sys, 'ps1') or not sys.stderr.isatty():
            sys.__excepthook__(type, value, tb)
        else:
            traceback.print_exception(type, value, tb)
            pdb.post_mortem(tb)

    sys.excepthook = info


def cli(args=None):
    main_parser = argparse.ArgumentParser(
        prog='photostack',
        description='Chainable, non-generative photo orientation and blending tools.',
    )
    main_parser.add_argument('--pdb', action='store_true')
    # collection of shared options
    shared_parser = argparse.ArgumentParser(add_help=False)
    shared_parser.add_argument('--pdb', action='store_true')
    shared_parser.add_argument('--verbose', '-v', default=1, action='count')
    shared_parser.add_argument(
        '--overwrite',
        action='store_true',
        help='replace output files that already exist',
    )
    command_parser = main_parser.add_subparsers(dest='command')
    parsers = {
        'main': main_parser,
        'shared': shared_parser,
        'command': command_parser,
    }
    pm = get_plugin_manager()
    pm.hook.photostack_addoption(
        parser=main_parser, parsers=parsers, pluginmanager=pm
    )
    # handle actual options
    ns = main_parser.parse_args(args)
    if ns.command is None:
        main_parser.print_help()
        sys.exit(1)
    return ns


def main():
    ns = cli()
    if 'pdb' in ns and ns.pdb:
        attach_debugger()
    logs.configure(ns.verbose)
    try:
        ns.func(ns)
    except (PhotoStackError, OSError) as exc:
        print(f'photostack: error: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    main()
