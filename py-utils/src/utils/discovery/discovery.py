#!/bin/python3

# CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.

import argparse
import errno
import inspect
import os
import sys
import traceback

from cortx.utils.discovery.node_health_generator import NodeHealthGenerator


class Cmd:
    """Discovery command handler class."""

    def __init__(self, args: dict):
        self._args = args
        self._script_dir = os.path.dirname(os.path.abspath(__file__))
        self.nh_gen = NodeHealthGenerator()

    @property
    def args(self) -> str:
        return self._args

    @staticmethod
    def usage(prog: str):
        """Print usage instructions."""
        sys.stderr.write(f"""{prog}
            [ -h|--help ]
            [ discover ]
            [ show --health [<rpath>] ]
            \n""")

    @staticmethod
    def get_command(desc: str, argv: dict):
        """Return the Command after parsing the command line."""
        if not argv:
            return
        parser = argparse.ArgumentParser(desc)
        subparsers = parser.add_subparsers()
        cmds = inspect.getmembers(sys.modules[__name__])
        cmds = [(x, y) for x, y in cmds
            if x.endswith("Cmd") and x != "Cmd"]
        for name, cmd in cmds:
            cmd.add_args(subparsers, cmd, name)
        args, unknown = parser.parse_known_args(argv)
        args.args = unknown + args.args
        return args.command(args)

    @staticmethod
    def add_args(parser: str, cls: str, name: str):
        """Add Command args for parsing."""
        parsers = parser.add_parser(cls.name, help="%s" % cls.__doc__)
        parsers.add_argument("args", nargs="*", default=[], help="args")
        parsers.set_defaults(command=cls)


class DiscoverCmd(Cmd):
    """Generate resource health map."""

    name = "discover"

    def __init__(self, args: dict):
        """Initialize discover command."""
        super().__init__(args)

    @staticmethod
    def add_args(parser: str, cls: str, name: str):
        """Add Command args for parsing."""
        parsers = parser.add_parser(cls.name, help="%s" % cls.__doc__)
        parsers.add_argument("args", nargs="*", default=[], help="args")
        parsers.set_defaults(command=cls)

    def process(self):
        """Process discover command."""
        self.nh_gen.generate()


class ShowCmd(Cmd):
    """Show health status for any resource path."""

    name = "show"

    def __init__(self, args):
        """Initialize show command."""
        super().__init__(args)

    @staticmethod
    def add_args(parser: str, cls: str, name: str):
        """Add Command args for parsing."""
        parsers = parser.add_parser(cls.name, help="%s" % cls.__doc__)
        parsers.add_argument("args", nargs="*", default=[],
            help="args")
        parsers.add_argument("--health", default="",
            help="Resource path")
        parsers.add_argument("--cached", action="store_false",
            help="Fetch health from cache if only '--cached' passed")
        parsers.set_defaults(command=cls)

    def process(self):
        """Show health information of given rpath."""
        health_info = self.nh_gen.get_node_health_info(
            rpath=self.args.health, cached=self.args.cached)
        sys.stdout.write("%s\n" % health_info)


def main(argv: dict):
    try:
        desc = "Discovery Interface"
        command = Cmd.get_command(desc, argv[1:])
        if not command:
            Cmd.usage(argv[0])
            return errno.EINVAL
        command.process()
    except Exception as e:
        sys.stderr.write("error: %s\n\n" % str(e))
        sys.stderr.write("%s\n" % traceback.format_exc())
        Cmd.usage(argv[0])
        return errno.EINVAL

if __name__ == "__main__":
    sys.exit(main(sys.argv))
