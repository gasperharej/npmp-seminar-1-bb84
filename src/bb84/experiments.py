from bb84.protocol import run_bb84, sift_transmissions
from bb84.analysis import calculate_qber, select_control_sample


def main():
    transmissions = run_bb84(1000, noise_level=0.2)
    sifted = sift_transmissions(transmissions)

    control, remaining = select_control_sample(sifted, 100)

    print("Obdržanih:", len(sifted))
    print("Kontrolni vzorec:", len(control))
    print("Preostalih:", len(remaining))
    print(f"QBER vzorca: {calculate_qber(control):.2%}")


if __name__ == "__main__":
    main()