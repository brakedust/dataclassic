# from koala.dataclasses import dataclass, post_init_coersion, argument
# from dataclasses import dataclass
import sys
from pathlib import Path

from dataclassic.commandline import Program, argument

# from dataclasses import fields, MISSING
# import pytest
prog = Program("booyeah")

COMPARE_VAL = None


@prog.command("Greet")
class greet:
    """
    Gives a greeting to our hero.
    """

    name: list[str] = argument(doc="Name of the hero", nargs=2)
    numbers: list[int] = argument(doc="favorite numbers", nargs="+")  # , converter=list[int])
    language: str = argument(default="English", doc="Language spoken", alias="-l")
    is_blue: bool = argument(is_flag=True)

    def execute(self, *args):
        global COMPARE_VAL
        val = f"Hello.  {self.name[0]} {self.name[1]}'s favorite numbers are {', '.join(str(x) for x in self.numbers)} and they speak {self.language}."  # nopep8
        if self.is_blue:
            val += "\nThey are BLUE!!"
        print(val)
        COMPARE_VAL = val


sys.argv = [Path(__file__).name, "greet", "Paul", "Bunyan", "1", "30"]

prog.print_parsed_command_line(prog.parse_command_line())

sys.argv = [Path(__file__).name, "GreeT", "--help"]
prog.parse_and_execute()

print("\n----------------------------\n")
sys.argv = [Path(__file__).name, "--help"]
prog.parse_and_execute()

print("\n----------------------------\n")
sys.argv = [Path(__file__).name]
prog.parse_and_execute()
