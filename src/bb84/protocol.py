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

    qc.measure(0,0)


def transmit(bit: int, alice_basis: str, bob_basis: str, eve_basis: str | None = None, noise_level: float = 0.0) -> int:
    """prenos kubita med alice in bobom (eve je lahko prisotna ali pa ne)"""

    # Ustvari kvantno vezje z 1 kubitom in 2 klasičnima bitoma - prvi je za boba, drugi za eve, da se vanj shranjujejo vrednosti emritev enega qubita ki ga imamo
    qc = QuantumCircuit(1, 2) 

    noise_model = NoiseModel() #prazen model šuma
    
    error = depolarizing_error(noise_level, 1) #depolarizacijska napaka velikosti noise_level, na edinem kubitu v vezju
    
    noise_model.add_all_qubit_quantum_error(error, ["id"]) #uporabi napako error na vsaki operaciji vrste id, ne glede na indeks kubita

    #Alice pripravi kubit
    prepare_state(qc, bit, alice_basis)

    if eve_basis is not None:
        interception(qc, eve_basis)

    #uporabimo id vrata na katerih se zgodi šum - v prenosu je samo en šum, ne npr na vsakih vratih
    qc.id(0)

    #Bob izmeri kubit
    measure_state(qc, bob_basis)

    # Izvede vezje s simulatorjem (shots=1) - izvede se en prenos kubita med alice in bobom
    simulator = AerSimulator(noise_model=noise_model) #simulator, ki upošteva model šuma
    result = simulator.run(qc, shots=1, memory=True).result()

    # Pridobmo Bobov izmerjeni bit
    memory = result.get_memory(qc)[0] #vrne npr. "10", kjer je 1 bit ki ga je izmerila eve, 0 pa bit ki ga je izmeril bob
    bob_measured_bit = memory[-1]

    return int(bob_measured_bit)


def run_bb84(n: int, interception_rate: float = 0.0, noise_level: float = 0.0) -> list[dict]:
    """Simulira n prenosov protokola BB84."""
    transmissions = []

    for _ in range(n):
        # Alicein naključni bit
        bit = random.randint(0, 1)

        # Aliceina naključna baza
        alice_basis = random.choice(["X", "Z"])

        # Eve prestreže vsak kubit in naključno izbere merilno bazo
        if random.random() < interception_rate:
            eve_basis = random.choice(["X", "Z"])
        else:
            eve_basis = None

        # Bobova naključna baza
        bob_basis = random.choice(["X", "Z"])

        # prenos
        measured_bit = transmit(bit, alice_basis, bob_basis, eve_basis, noise_level)

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