"""
==================
koala.commandline
==================

Do you love dataclasses and want to use them to write your next CLI?
Have we got the thing for you.  Using the @command decorator, you can
turn a dataclass into CLI that parses the command line.  Mix this with the
@dataclass and @post_init_coercion decorators and you're off to the races.


Example:

    @command
    @dataclass
    @post_init_coersion
    class greet:

        name: str = field(doc="Name of the hero", nargs=2)
        numbers: list[int] = field(doc="favorite numbers", nargs="+")
        language: str = field(default="English", doc="Language spoken")

        def execute(self):

            val = f"Hello.  {self.name[0]} {self.name[1]}'s favorite numbers are {', '.join(str(x) for x in self.numbers)} and they speak {self.language}."
            print(val)


"""
import sys
from functools import partial
from dataclasses import Field
from koala.dataclasses import fields, MISSING, JSON_SCHEMA_TYPES, dataclass, post_init_coersion, field as field_


class ParseError(Exception):
    pass


# @wraps(field_)
def field(*, is_flag=False, **kwargs) -> Field:

    if "metadata" not in kwargs:
        kwargs["metadata"] = {}

    kwargs["metadata"]['is_flag'] = is_flag

    if is_flag and ('default' not in kwargs):
        kwargs['default'] = False

    return field_(**kwargs)


class Program:

    def __init__(self, name=""):

        self.name = name

        self.commands = {}

        # self.exec_stack = []

        self.settings = None

    def command(self, cls: type=None, *, name=None):
        """This is a decorator"""
        return command(cls, name=name, program=self)
        # self.commands[cls.name] = cls

    def parse_command_line(self, args=None):

        exec_stack = []
        # names = [cmd.__name__ for cmd in self._commands]
        if not args:
            args = sys.argv[1:]

        print(f"{sys.argv=}")
        print(f"{args=}")

        if not args:
            # no arguments supplied in any way
            print(f"program: {self.name}")
            print("Available subcommands:")
            print("----------------------")
            for cmd in self.commands:
                print(cmd)
                return exec_stack

        # exec_stack = []
        lenargs = len(args)
        for iarg, arg in enumerate(args):

            if arg in self.commands.keys():
                exec_stack.append(
                    [iarg, arg, self.commands[arg]]
                )


        for i, cmd_info in enumerate(exec_stack):

            start_arg = cmd_info[0]
            end_arg = -1 if (i == len(exec_stack)-1) else exec_stack[i+1][0]
            if end_arg >= 0:
                cmd_info[2] = cmd_info[2].parse_args(args[start_arg+1:end_arg])
            else:
                cmd_info[2] = cmd_info[2].parse_args(args[start_arg+1:])

        return exec_stack


    def print_parsed_command_line(self, exec_stack):
        for i, cmd_info in enumerate(exec_stack):
            print(f"{i:00d}: {cmd_info[2]}")


    def execute(self, exec_stack):

        values = None
        for i, cmd_info in enumerate(exec_stack):
            values = cmd_info[2].execute(values)

        return values

    def parse_and_execute(self, args=None):

        stack = self.parse_command_line(args)
        if stack:
            return self.execute(stack)


def make_alias(f: Field, opt: dict[str, Field]):
    """
    If an alias has not been explicitly defined, make a one letter alias
    and see if it has been taken yet.  If not, add an entry into the
    options dictionary
    """
    alias = f.metadata.get('alias', None)
    if alias:
        opt[alias] = f
    else:
        maybe_alias = '-' + f.metadata["shell_name"].strip('-')[0]
        if not maybe_alias in opt:
            opt[maybe_alias] = f
            f.metadata['alias'] = maybe_alias


def command(cls: type=None, *, name=None, program=None):
    """
    Decorator to make a dataclass parse command line arguments

    @command
    @dataclass
    def do_something:
        pass

    @command(name="do-something")
    @dataclass
    def do_something:
        pass
    """

    def wrapper(cls):
        return command(cls, name=name, program=program)

    if cls is None:
        return wrapper

    cls.name = name if name else cls.__name__

    # if not hasattr(cls, "__post_init__"):
    # cls = post_init_coersion(cls)

    program.commands[cls.name] = cls

    cls._options = {}
    cls._arguments = []
    # cls._flags = {}
    for i, f in enumerate(fields(cls)):
        f.metadata = dict(f.metadata)

        if f.metadata.get("is_flag", False):
            f.metadata["nargs"] = 0
            f.metadata["shell_name"] = f"--{f.name}"
            cls._options[f.metadata["shell_name"]] = f
            make_alias(f, cls._options)

        elif (f.default != MISSING):
            f.metadata["shell_name"] =  f"--{f.name}"
            cls._options[f.metadata["shell_name"]] = f
            make_alias(f, cls._options)
        else:
            f.metadata["shell_name"] = f.name
            cls._arguments.append(f)


    @classmethod
    def parse_args(cls, inargs=None):
        if inargs is None:
            inargs = sys.argv[1:]

        if "-h" in inargs or "--help" in inargs:
            print(cls.help())
            raise ParseError()

        # self = cls()
        args = []
        kwargs = {}

        # --------------------
        # Handle Options
        for shell_name, f in cls._options.items():
            # nargs = f.metadata["nargs"]
            if shell_name in inargs:
                nargs = f.metadata["nargs"]
                iarg = inargs.index(shell_name)
                _ = inargs.pop(iarg)

                if f.metadata.get("is_flag", False):
                    kwargs[cls._options[shell_name].name] = not f.default
                elif nargs == 1:
                    val = inargs.pop(iarg)
                    kwargs[cls._options[shell_name].name] = val
                elif nargs > 1:
                    val = [inargs.pop(iarg) for i in range(nargs)]
                    kwargs[cls._options[shell_name].name] = val

        #----------------------
        # look for unknown options
        found_unknown_arg = False
        errs = []
        for arg in inargs:
            if isinstance(arg, str) and arg.startswith("-"):
                found_unknown_arg = True
                errs.append(f"Unknown argument [{arg}] found in command [{cls.__name__}]")

        if found_unknown_arg:
            raise ParseError("\n".join(errs))

        #----------------------
        # Handle positional arguments
        args = []
        for f in cls._arguments:
            nargs = f.metadata.get("nargs", 1)
            if nargs in ('*',):
                args.append(list(inargs))
                inargs = []
            if nargs in ('+',):
                if len(inargs) == 0:
                    # sys.stderr.writelines([f"No arguments specified for argument [{f.name}] in command [{cls.__name__}] which requires at least one"])
                    raise ParseError(f"No arguments specified for argument [{f.name}] in command [{cls.__name__}] which requires at least one")
                args.append(list(inargs))
                inargs = []
            elif nargs == 1:
                args.append(inargs.pop(0))
            elif nargs > 1:
                args.append([inargs.pop(0) for i in range(nargs)])

        assert len(inargs) == 0

        try:
            self = cls(*args, **kwargs)
        except Exception as ex:
            print(ex.args[0])
            raise ParseError(ex)


        return self

    @classmethod
    def help(cls):
        text = []
        text.append(f"{cls.name}")
        text.append("\nPositional Arguments\n--------------------")
        for f in cls._arguments:
            text.append(f"{f.name} \n    type = {JSON_SCHEMA_TYPES[f.type]}\n    count = {f.metadata.get('nargs',1)}")

        text.append("\nOptions\n--------------------")
        for f in set(cls._options.values()):
            shell_name = f.metadata["shell_name"]
            alias = f.metadata.get('alias', None)
            if alias:
                name = f"{shell_name}/{alias}"
            else:
                name = shell_name
            if f.metadata.get("is_flag", False):
                text.append(f"{name} \n    type = boolean flag\n    default = {f.default}")
            else:
                text.append(f"{name} \n    type = {JSON_SCHEMA_TYPES[f.type]}\n    count = {f.metadata.get('nargs', 1)}\n    default = {f.default}")

        return "\n".join(text)

    cls.parse_args = parse_args
    cls.help = help

    return cls
