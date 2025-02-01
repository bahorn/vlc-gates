from enum import Enum


class BristolCircuitStates(Enum):
    DEF = 0
    INOUT = 1
    GATE = 2


class BristolCircuit:
    """
    Loader for the Bristol Circuit format.

    We offset the wires by 2 as wires 0 and 1 store 0 and 1 respectively.
    """

    def __init__(self):
        self._state = BristolCircuitStates.DEF
        self._gates = []
        self._wires = []
        self._in_1_wires = []
        self._in_2_wires = []
        self._out_wires = []

    def add_line(self, line):
        res = line.split()

        if len(res) == 0:
            return

        match self._state:
            case BristolCircuitStates.DEF:
                assert len(res) == 2
                self._n_gates = int(res[0])
                self._wires = list(range(2, int(res[1]) + 2))
                self._state = BristolCircuitStates.INOUT

            case BristolCircuitStates.INOUT:
                assert len(res) == 3
                self._n_in_1 = int(res[0])
                self._in_1_wires = self._wires[:self._n_in_1]
                self._n_in_2 = int(res[1])
                self._in_2_wires = self._wires[
                        self._n_in_1:self._n_in_1 + self._n_in_2
                    ]
                self._n_out = int(res[2])
                self._out_wires = self._wires[-self._n_out:]

                self._state = BristolCircuitStates.GATE

            case BristolCircuitStates.GATE:
                gate = res[-1]
                n_in = int(res[0])
                n_out = int(res[1])
                in_wires = list(map(lambda x: int(x) + 2, res[2:2 + n_in]))
                out_wires = list(
                    map(lambda x: int(x) + 2, res[2 + n_in:2 + n_in + n_out])
                )
                self._gates.append((gate, in_wires, out_wires))

    def gen(self):
        return (
            self._wires,
            self._in_1_wires,
            self._in_2_wires,
            self._out_wires,
            self._gates
        )


def loader(fname):
    with open(fname) as f:
        bc = BristolCircuit()
        for line in f:
            cleaned = line.strip()
            bc.add_line(cleaned)
        return bc.gen()


def test():
    import sys
    loader(sys.argv[1])


if __name__ == "__main__":
    test()
