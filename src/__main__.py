"""
Logic gates with VLC + m3us

yep...
"""
import os
import math
import sys
from bristol import loader


HOST = "http://:a@0/requests/vlm_cmd.xml?command="
def pause(f): return f'vlc://pause:{f}'
def vlm_cmd(cmd): return f'{HOST}{cmd}'


def wrap(cmd, lst):
    res = []

    for i in lst:
        res.append(cmd(i))
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


class InvGate(LUTGate):
    TABLE = {'0': '1', '1': '0'}


class OrGate(LUTGate):
    TABLE = {'00': '0', '10': '1', '01': '1', '11': '1'}


class XorGate(LUTGate):
    TABLE = {'00': '0', '10': '1', '01': '1', '11': '0'}


class AndGate(LUTGate):
    TABLE = {'00': '0', '10': '0', '01': '0', '11': '1'}


def main():
    # setup
    start = []
    start += ['./main.m3u']

    write('./start.m3u', '\n'.join(start))

    wires, in_1_wires, in_2_wires, out_wires, gates = loader(sys.argv[1])

    # create all the wires
    for wire in wires:
        os.system(f'printf 0 > ./pins/{wire}')

    # copy the input into the two inputs
    with open(sys.argv[2]) as f:
        for value, wire in zip(f, in_1_wires):
            v = value.strip()
            os.system(f'printf {v} > ./pins/{wire}')
        f.close()

    with open(sys.argv[3]) as f:
        for value, wire in zip(f, in_2_wires):
            v = value.strip()
            os.system(f'printf {v} > ./pins/{wire}')
        f.close()

    # setup the circuit
    ag = AndGate()
    xg = XorGate()
    ig = InvGate()
    body = []

    for gate_type, gate_in, gate_out in gates:
        g_in = list(map(lambda x: f'./pins/{x}', gate_in))
        g_out = f'./pins/{gate_out[0]}'
        match gate_type:
            case 'AND':
                body += ag.evaluate(g_in, g_out)
            case 'XOR':
                body += xg.evaluate(g_in, g_out)
            case 'INV':
                body += ig.evaluate(g_in, g_out)
            case _:
                raise Exception('unimplemented')

    # print the output
    body += copy('./prefix', './done.m3u', append=False)
    for pin_raw in out_wires:
        pin = f'./pins/{pin_raw}'
        body += copy(pin, './done.m3u', append=True)
        body += copy('./space', './done.m3u', append=True)
    body += copy('./postfix', './done.m3u', append=True)

    # loop endlessly
    body += ['./done.m3u', './main.m3u']

    # interleave pauses every few steps for perf reasons
    res = []
    for i, cmd in enumerate(body):
        if i % 5 == 0:
            res.append(pause(0.25))
        res.append(cmd)

    write('./main.m3u', '\n'.join(res))


if __name__ == "__main__":
    main()
