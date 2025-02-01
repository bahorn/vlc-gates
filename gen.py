"""
Logic gates with VLC + m3us

yep...
"""
import math

HOST = "http://:a@0/requests/vlm_cmd.xml?command="
def pause(f): return f'vlc://pause:{f}'
def vlm_cmd(cmd): return f'{HOST}{cmd}'


def wrap(cmd, lst):
    res = []

    for i in lst:
        res.append(cmd(i))
        res.append(pause(0.25))
    return res


def write(fname, contents):
    with open(fname, 'w') as f:
        f.write(contents)


def vod(name, options):
    base = ['new', name, 'vod', 'enabled']
    for option, value in options:
        base.append(option)
        base.append(value)
    return ' '.join(base)


def copy(fin, fout, name='b', append=False):
    """
    Copy fin to fout
    """
    rest = []
    if append:
        rest.append(('option', 'demuxdump-append%3dtrue'))

    v = vod(
        name,
        [
            ('input', fin),
            ('option', f'demuxdump-file%3d{fout}'),
            ('option', 'demux%3ddump')
        ] + rest
    )
    return wrap(vlm_cmd, [v, f'del {name}'])


class LUTGate:
    """
    Implement a Lookup Table Gate.
    """

    def __init__(self):
        name = type(self).__name__
        count = math.isqrt(len(self.TABLE))
        self._inputs = [f'./intermediate/in_{i}' for i in range(count)]
        self._output = './intermediate/out'
        self._eval = './intermediate/eval'
        self._prolog1 = f'./gates/{name}_p1'
        self._prolog2 = f'./gates/{name}_p2'
        self._epilog = f'./gates/{name}_epilog'

        for key, value in self.TABLE.items():
            write(f'./gates/{name}{key}', value)
        # now our prologue and epilogs
        c = '\n'.join(copy(f'./gates/{name}', self._output))
        prolog, epilog = c.split(f'{name}')
        # for some reason vlc did not like it when i had this all on one
        # line...
        write(self._prolog1, prolog[:7])
        write(self._prolog2, prolog[7:] + name)
        write(self._epilog, epilog)

    def evaluate(self, pins, out):
        """
        Evaluate with a given pin.
        """
        res = []
        # copy the input in
        for p, i in zip(pins, self._inputs):
            res += copy(p, i)
        # setup the gate
        res += copy(self._prolog1, self._eval, append=False)
        res += copy(self._prolog2, self._eval, append=True)
        for i in self._inputs:
            res += copy(i, self._eval, append=True)
        res += copy(self._epilog, self._eval, append=True)
        # call the gate
        res += [self._eval]
        # Copy the output out
        res += copy(self._output, out)
        return res


class Buf(LUTGate):
    TABLE = {'0': '0', '1': '1'}


class NotGate(LUTGate):
    TABLE = {'0': '1', '1': '0'}


class OrGate(LUTGate):
    TABLE = {'00': '0', '10': '1', '01': '1', '11': '1'}


class XorGate(LUTGate):
    TABLE = {'00': '0', '10': '1', '01': '1', '11': '0'}


class AndGate(LUTGate):
    TABLE = {'00': '0', '10': '0', '01': '0', '11': '1'}


def main():
    output = ['./pins/3', './pins/3']
    # setup
    start = []
    start += ['./main.m3u']

    write('./start.m3u', '\n'.join(start))

    # main
    ag = AndGate()
    ng = NotGate()
    body = []
    # evaluate our circuit
    body += ag.evaluate(['./pins/1', './pins/1'], './pins/2')
    body += ng.evaluate(['./pins/2'], './pins/3')
    body += copy('./prefix', './done.m3u', append=False)
    for pin in output:
        body += copy(pin, './done.m3u', append=True)
        body += copy('./space', './done.m3u', append=True)
    body += copy('./postfix', './done.m3u', append=True)
    # loop endlessly
    body += ['./done.m3u', './main.m3u']

    write('./main.m3u', '\n'.join(body))


if __name__ == "__main__":
    main()
