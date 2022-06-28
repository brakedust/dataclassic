# from koala.dataclasses import dataclass, post_init_coersion, field
# from dataclasses import dataclass

import sys
from tests._test_tools import Raises

from dataclassic.commandline import ParseError, command, Program, field, dataclass

# from dataclasses import fields, MISSING
# import pytest
prog = Program("booyeah")


@prog.command
@dataclass
class greet:

    name: str = field(doc="Name of the hero", nargs=2)
    numbers: list[int] = field(
        doc="favorite numbers", nargs="+"
    )  # , converter=list[int])
    language: str = field(default="English", doc="Language spoken")
    is_blue: bool = field(is_flag=True)

    def execute(self, *args):

        val = f"Hello.  {self.name[0]} {self.name[1]}'s favorite numbers are {', '.join(str(x) for x in self.numbers)} and they speak {self.language}."  # nopep8
        if self.is_blue:
            val += "\nThey are BLUE!!"
        print(val)
        return val


def test_parse_sys_argv():
    _argv = sys.argv
    # sys.argv = ["cmdline", "Super", "Bot", "42","17", "19", "--language", "Spanish"]
    sys.argv = ["dummy", "greet", "Super", "Bot", 1, "2", "--language", "Spanish"]
    # cmd = prog.parse_command_line()
    # s = cmd.execute()
    # prog.parse_command_line()
    s = prog.parse_and_execute()
    sys.argv = _argv
    assert s == "Hello.  Super Bot's favorite numbers are 1, 2 and they speak Spanish."


def test_parse_passed_args():

    # sys.argv = ["cmdline", "Super", "Bot", "42","17", "19", "--language", "Spanish"]
    args = ["greet", "Super", "Bot", 1, "2", "--language", "Spanish"]
    # cmd = greet.parse_args(args)
    # s = cmd.execute()
    # prog.parse_command_line(args)
    # s = prog.execute()
    s = prog.parse_and_execute(args)
    assert s == "Hello.  Super Bot's favorite numbers are 1, 2 and they speak Spanish."


def test_error():
    args = ["dummy", "greet", "Super", "Bot", "a", "2", "--language", "Spanish"]

    with Raises(ParseError) as r:
        # cmd = greet.parse_args(args)
        # prog.parse_command_line(args)
        # s = prog.execute()
        s = prog.parse_and_execute(args)

        assert True

    assert True


def test_pipeline_program():

    args = [
        "greet",
        "Super",
        "Bot",
        "1",
        "2",
        "--is_blue",
        "--language",
        "Spanish",
        "greet",
        "Guy",
        "Fieri",
        8,
        19,
        77,
        92,
    ]
    # prog.parse_command_line(args)
    # Program.print_parsed_command_line()
    # prog.execute()
    s = prog.parse_and_execute(args)


# test_parse_passed_args()
