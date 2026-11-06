# Literatura

Tri izbrana dela pokrivajo protokol, šum in zaznavanje pri omejenem kontrolnem vzorcu. Priporočen je spodnji vrstni red branja.

## 1. BB84 in simulacija

**Mihai-Zicu Mina in Emil Simion (2020).** *A Scalable Simulation of the BB84 Protocol Involving Eavesdropping.* Cryptology ePrint Archive, 2020/1074, prednatis. [PDF — arhivska kopija](https://web.archive.org/web/20240901000000id_/https://eprint.iacr.org/2020/1074.pdf) · [Metapodatki](https://eprint.iacr.org/2020/1074)

Članek uporabimo za razumevanje korakov Alice, Boba in Eve ter napada intercept-resend. Najprej preberemo opis protokola in napada, nato razlago simulacije v Qiskitu. Primeri iz leta 2020 uporabljajo starejše API-je, zato aktualne klice preverimo v uradni dokumentaciji.

## 2. Šum in prisluškovanje

**Francesco Fiorini, Michele Pagano, Rosario Giuseppe Garroppo in Antonio Osele (2024).** *Estimating Interception Density in the BB84 Protocol: A Study with a Noisy Quantum Simulator.* Future Internet, 16(8), 275. [PDF](https://www.mdpi.com/1999-5903/16/8/275/pdf) · [DOI](https://doi.org/10.3390/fi16080275)

Članek pokaže, zakaj je pri opazovanju QBER treba upoštevati tudi šum in ne samo Eve. Osredotočimo se na opis delnega prestrezanja, uporabljeni šumni simulator in vrednotenje ocen gostote prestrezanja. Njihovo metodo primerjamo s svojim načrtom zaznavanja; dolžina ključa ni samodejno enaka velikosti našega javno preverjenega vzorca.

## 3. Zaznavanje in kontrolni vzorec

**Chankyun Lee, Eunjoo Lee in Wonhyuk Lee (2023).** *Analysis on Eavesdropper Detection in BB84 Quantum Key Distribution Protocol against Partial Intercept-and-resend Attack.* 2023 International Conference on Optical Network Design and Modeling (ONDM). [PDF](https://dl.ifip.org/db/conf/ondm/ondm2023/1570879964.pdf)

To je neposredna podlaga za H1 in H3: povezuje število javno preverjenih bitov s pragom zaznavanja ter lažnimi alarmi in spregledanimi napadi. Preberemo razdelek II za pomen metrik, III za prag odločanja in IV za primerjavo nastavitev. Njihovega približnega modela QBER ne obravnavamo kot zagotovilo za delovanje našega prihodnjega detektorja.

## Prenos

Po aktivaciji razvojnega okolja zaženemo:

```bash
python scripts/fetch_literature.py
```

Manifest `sources.json` vsebuje samo te tri članke, citati pa so v `references.bib`. Skripta shranjuje v `literature/pdfs/`, preveri obliko PDF in preskoči že veljavne datoteke; ob napaki izpiše povezavo za ročni prenos in vrne kodo 1. PDF-ji so prezrti v Gitu. Za Fiorini idr. je na voljo tudi [institucionalni repozitorij](https://arpi.unipi.it/handle/11568/1271727).

Za Mina–Simion uporabljamo preverjeno arhivsko kopijo istega odprtega prednatisa, ker [izvirni PDF](https://eprint.iacr.org/2020/1074.pdf) vrača HTTP 403 pri samodejnem prenosu. Letnica 2020 velja za citirani prednatis; založniška različica istega dela je izšla leta [2021](https://doi.org/10.1007/978-3-030-69255-1_7).

## Prejšnje lokalne kopije

Naslednje datoteke niso več del izbrane zbirke; ostanejo na disku in se ne prenašajo več samodejno:

- `01_bennett_brassard_1984_bb84.pdf`
- `02_gisin_2002_quantum_cryptography.pdf`
- `03_scarani_2009_practical_security.pdf`
- `04_cai_scarani_2009_finite_key.pdf`
- `05_tomamichel_2012_tight_finite_key.pdf`
- `07_shor_preskill_2000_security_proof.pdf`

## Dokumentacija orodij

- [Qiskit Aer — AerSimulator](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator.html)
- [SciPy — binomtest](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html)
