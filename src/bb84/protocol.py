from qiskit import QuantumCircuit


def prepare_state(qc: QuantumCircuit, bit: int, basis: str) -> None:
    """Pripravi stanje BB84 iz začetnega |0>."""
    if bit == 1:
        qc.x(0)
    if basis == "X":
        qc.h(0)
    else:
        pass
        
        


def measure_state(qc: QuantumCircuit, basis: str) -> None:
    """Izmeri kubit v izbrani bazi."""
    if basis == "Z":
        qc.measure(0,0)
    else:
        qc.h(0)
        qc.measure(0,0)