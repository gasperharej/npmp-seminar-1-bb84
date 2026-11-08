import random

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error


def prepare_state(qc: QuantumCircuit, bit: int, basis: str) -> None:
    """Pripravi stanje iz začetnega |0>."""
    if bit == 1:
        qc.x(0)
    if basis == "X":
        qc.h(0)


def interception(qc: QuantumCircuit, basis: str) -> None:
    """Eve prestreže in izmeri kubit v izbrani bazi."""

    if basis == "Z":
        qc.measure(0, 1)
    else:
        qc.h(0)
        qc.measure(0, 1)
        qc.h(0)


def measure_state(qc: QuantumCircuit, basis: str) -> None:
    """Izmeri kubit v izbrani bazi."""
    if basis == "X":
        qc.h(0)

    qc.measure(0, 0)


def transmit(
    bit: int,
    alice_basis: str,
    bob_basis: str,
    simulator: AerSimulator,
    eve_basis: str | None = None,
    noise_level: float = 0.0,
) -> int:
    """Prenese kubit; šum določa podani simulator, ne ta funkcija.

    ``noise_level`` je opuščen argument: za združljivost sprejmemo le 0.
    """
    if noise_level != 0:
        raise ValueError("Configure noise on simulator; transmit does not apply noise_level")
    if bit not in (0, 1) or alice_basis not in ("X", "Z") or bob_basis not in ("X", "Z"):
        raise ValueError("Expected a binary bit and X/Z bases")
    if eve_basis not in (None, "X", "Z"):
        raise ValueError("Expected Eve basis X, Z or None")

    # Bobov izid gre v c[0], Evejin v c[1]. Kolaps stanja izvede intercept-resend.
    qc = QuantumCircuit(1, 2)

    # Alice pripravi kubit
    prepare_state(qc, bit, alice_basis)

    if eve_basis is not None:
        interception(qc, eve_basis)

    # uporabimo id vrata na katerih se zgodi šum - v prenosu je samo en šum, ne npr na vsakih vratih
    qc.id(0)

    # Bob izmeri kubit
    measure_state(qc, bob_basis)

    # Izvede vezje s simulatorjem (shots=1) - izvede se en prenos kubita med alice in bobom
    result = simulator.run(
        qc,
        shots=1,
        memory=True,
        seed_simulator=random.randrange(1, 2**31),
    ).result()

    # Pridobmo Bobov izmerjeni bit
    memory = result.get_memory(qc)[0]  # "10" pomeni Eve=1, Bob=0.
    bob_measured_bit = memory[-1]

    return int(bob_measured_bit)


def run_bb84(n: int, interception_rate: float = 0.0, noise_level: float = 0.0) -> list[dict]:
    """Simulira n prenosov protokola BB84."""
    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a nonnegative integer")
    if not 0 <= interception_rate <= 1 or not 0 <= noise_level <= 1:
        raise ValueError("interception_rate and noise_level must be between 0 and 1")
    transmissions = []

    noise_model = NoiseModel()
    error = depolarizing_error(noise_level, 1)
    noise_model.add_all_qubit_quantum_error(error, ["id"])

    simulator = AerSimulator(
        noise_model=noise_model,
        max_parallel_threads=1,
    )  # simulator, ki upošteva model šuma

    for _ in range(n):
        # Alicein naključni bit
        bit = random.randint(0, 1)

        # Aliceina naključna baza
        alice_basis = random.choice(["X", "Z"])

        # Eve z določeno verjetnostjo prestreže kubit in izbere naključno merilno bazo
        if random.random() < interception_rate:
            eve_basis = random.choice(["X", "Z"])
        else:
            eve_basis = None

        # Bobova naključna baza
        bob_basis = random.choice(["X", "Z"])

        # prenos
        measured_bit = transmit(bit, alice_basis, bob_basis, simulator, eve_basis)

        measurement = {
            "alice_bit": bit,
            "alice_basis": alice_basis,
            "eve_basis": eve_basis,
            "bob_basis": bob_basis,
            "bob_bit": measured_bit,
        }

        transmissions.append(measurement)

    return transmissions


def sift_transmissions(transmissions: list[dict]) -> list[dict]:
    """Obdrži prenose, kjer sta Alice in Bob izbrala isto bazo."""
    sifted = []

    for transmission in transmissions:
        if transmission["alice_basis"] == transmission["bob_basis"]:
            sifted.append(transmission)

    return sifted
