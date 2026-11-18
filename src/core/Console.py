import shlex

# simple command system
class Console:
    def __init__(self):
        self._cmds = {}
        # register help by default
        self.register("help", self._help)

    def register(self, name, fn):
        # add command handler
        self._cmds[name] = fn

    def execute(self, inp):
        # parse and run command
        try:
            parts = shlex.split(inp)
        except:
            return "parse error"
        if not parts:
            return ""
        cmd, *args = parts
        fn = self._cmds.get(cmd)
        if not fn:
            return f"unknown: {cmd}"
        return fn(args)

    def _help(self, args):
        # list all registered commands
        return "commands:\n" + "\n".join(f"  {n}" for n in sorted(self._cmds))
