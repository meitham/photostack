
import pluggy

hookspec = pluggy.HookspecMarker("photostack")


@hookspec
def photostack_addoption(parser, parsers, pluginmanager):
    """Add command line options to the parser.

    Called once at the beginning of a session to register argparse options.
    """
