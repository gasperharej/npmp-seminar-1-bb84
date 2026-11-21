import random
from unittest.mock import MagicMock

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from bb84 import protocol
from bb84.analysis import calculate_qber


@pytest.mark.parametrize(
    "bit,basis,label", [(0, "Z", "0"), (1, "Z", "1"), (0, "X", "+"), (1, "X", "-")]
)
def test_four_states(bit, basis, label):
    circuit = QuantumCircuit(1)
    protocol.prepare_state(circuit, bit, basis)
    assert Statevector.from_instruction(circuit).equiv(Statevector.from_label(label))


@pytest.mark.parametrize("basis", ["X", "Z"])
@pytest.mark.parametrize("bit", [0, 1])
@pytest.mark.parametrize("eve", [None, "X", "Z"])
def test_measurements_and_single_channel_location(basis, bit, eve):
    capture = MagicMock()
    capture.run.return_value.result.return_value.get_memory.return_value = ["10"]
    assert protocol.transmit(bit, basis, basis, capture, eve) == 0  # c[0], ne c[1]
    circuit = capture.run.call_args.args[0]
    names = [item.operation.name for item in circuit.data]
    assert names.count("id") == 1
    measurements = [i for i, name in enumerate(names) if name == "measure"]
    assert names.index("id") < measurements[-1]
    if eve:
        assert measurements[0] < names.index("id")
    counts = (
        AerSimulator(max_parallel_threads=1)
        .run(circuit, shots=4096, seed_simulator=123)
        .result()
        .get_counts()
    )
    error_rate = sum(n for bits, n in counts.items() if int(bits[-1]) != bit) / 4096
    assert error_rate == 0 if eve in (None, basis) else abs(error_rate - 0.5) < 0.04


@pytest.mark.parametrize(
    "noise,rate", [(0, 0), (0, 1), (0.06, 0), (0.2, 0.2), (0.4, 0.5), (0.5, 0), (0.5, 1), (1, 0)]
)
def test_qber_matches_channel_model(noise, rate):
    random.seed(84501)
    transmissions = protocol.run_bb84(6000, rate, noise)
    sifted = protocol.sift_transmissions(transmissions)
    qber, _, count = calculate_qber(sifted)
    expected = noise / 2 + (1 - noise) * rate / 4
    assert 2700 < count < 3300
    assert all(t["alice_basis"] == t["bob_basis"] for t in sifted)
    assert abs(qber - expected) <= 6 * np.sqrt(expected * (1 - expected) / count)
    intercepted = sum(t["eve_basis"] is not None for t in transmissions)
    assert abs(intercepted / 6000 - rate) <= 0.04


def test_one_simulator_reused_per_transmission_batch(monkeypatch):
    simulators = []

    def record(bit, alice_basis, bob_basis, simulator, eve_basis):
        simulators.append(simulator)
        return bit

    monkeypatch.setattr(protocol, "transmit", record)
    protocol.run_bb84(5, 0.2, 0.1)
    assert len(simulators) == 5
    assert all(simulator is simulators[0] for simulator in simulators)


@pytest.mark.parametrize(
    "args", [(-1, 0, 0), (2, -0.1, 0), (2, 1.1, 0), (2, 0, -0.1), (2, 0, 1.1), (2, 0, float("nan"))]
)
def test_invalid_protocol_parameters(args):
    with pytest.raises(ValueError):
        protocol.run_bb84(*args)
