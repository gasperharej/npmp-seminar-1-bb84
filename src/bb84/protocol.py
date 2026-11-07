from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import random


def prepare_state(qc: QuantumCircuit, bit: int, basis: str) -> None:
    """Pripravi stanje BB84 iz začetnega |0>."""
    if bit == 1:
        qc.x(0)
    if basis == "X":
        qc.h(0)
    else:
        pass   


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
    if basis == "Z":
        qc.measure(0,0)
    else:
        qc.h(0)
        qc.measure(0,0)


def transmit(bit: int, alice_basis: str, bob_basis: str, eve_basis: str | None = None) -> int:

    # Ustvari kvantno vezje z 1 kubitom in 2 klasičnima bitoma - prvi je za boba, drugi za eve, da se vanj shranjujejo vrednosti emritev enega qubita ki ga imamo
    qc = QuantumCircuit(1, 2) 

    #Alice pripravi kubit
    prepare_state(qc, bit, alice_basis)

    if eve_basis is not None:
        interception(qc, eve_basis)

    #Bob izmeri kubit
    measure_state(qc, bob_basis)

    # Izvede vezje s simulatorjem (shots=1) - izvede se en prenos kubita med alice in bobom
    simulator = AerSimulator()
    result = simulator.run(qc, shots=1, memory=True).result()

    # Pridobmo Bobov izmerjeni bit
    memory = result.get_memory(qc)[0] #vrne npr. "10", kjer je 1 bit ki ga je izmerila eve, 0 pa bit ki ga je izmeril bob
    bob_measured_bit = memory[-1]

    return int(bob_measured_bit)


def run_bb84(n: int, intercepted: bool = False) -> list[dict]:
    """Simulira n prenosov protokola BB84."""
    transmissions = []

    for _ in range(n):
        # Alicein naključni bit
        bit = random.randint(0, 1)

        # Aliceina naključna baza
        alice_basis = random.choice(["X", "Z"])

        # Eve prestreže vsak kubit in naključno izbere merilno bazo
        if intercepted:
            eve_basis = random.choice(["X", "Z"])
        else:
            eve_basis = None

        # Bobova naključna baza
        bob_basis = random.choice(["X", "Z"])

        # prenos
        measured_bit = transmit(bit, alice_basis, bob_basis, eve_basis)

        measurement = {
                "alice_bit": bit,
                "alice_basis": alice_basis,
                "eve_basis": eve_basis,
                "bob_basis": bob_basis,
                "bob_bit": measured_bit
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


def calculate_qber(sifted: list[dict]) -> float:
    """Izračuna delež napak med obdržanimi biti."""
    if not sifted:
        raise ValueError("No sifted bits available")

    errors = 0

    for transmission in sifted:
        if transmission["alice_bit"] != transmission["bob_bit"]:
            errors += 1

    return errors / len(sifted)


normal = sift_transmissions(run_bb84(1000))
attacked = sift_transmissions(run_bb84(1000, intercepted=True))

print("Brez Eve:")
print("Obdržanih bitov:", len(normal))
print("QBER:", calculate_qber(normal))

print("\nZ Eve:")
print("Obdržanih bitov:", len(attacked))
print("QBER:", calculate_qber(attacked))