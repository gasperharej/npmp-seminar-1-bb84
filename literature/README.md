# Literatura in metodološka razmejitev

## Mina in Simion (2020)

*A Scalable Simulation of the BB84 Protocol Involving Eavesdropping.* [Prednatis 2020/1074](https://eprint.iacr.org/2020/1074), [arhivski PDF](https://web.archive.org/web/20240901000000id_/https://eprint.iacr.org/2020/1074.pdf).

Razdelek 2 (str. 2–5 prednatisa) opisuje BB84, uskladitev baz in intercept-resend. Za idealni kanal in polni napad podajo zaznavo vsaj ene napake z verjetnostjo `1 − (3/4)^m`. Razdelek 3 opisuje dve izvedbi Qiskit in preizkuse simulatorja. To podpira osnovno preverjanje našega protokola, ne detektorja v šumu pri fiksnem α. Klice starega API je treba prilagoditi aktualnemu Qiskitu.

Citiramo prednatis iz 2020; založniška različica je izšla leta [2021](https://doi.org/10.1007/978-3-030-69255-1_7).

## Fiorini, Pagano, Garroppo in Osele (2024)

*Estimating Interception Density in the BB84 Protocol: A Study with a Noisy Quantum Simulator.* Future Internet 16(8), 275. [DOI](https://doi.org/10.3390/fi16080275), [PDF](https://www.mdpi.com/1999-5903/16/8/275/pdf), [institucionalna kopija](https://arpi.unipi.it/handle/11568/1271727).

Razdelki 4–6 opisujejo Quantum Solver, ocenjevanje gostote prestrezanja in primerjavo idealnega `aer_simulator` s šumnim `fake_brooklin` (tako zapisan v članku). V razdelku 6.2 uporabijo prestrezanja `{0; 0,2; 0,4; 0,6; 0,8; 1}`, 50 neodvisnih ponovitev in dolžine poslanih nizov 1024, 1536, 2048, 4096. V seznamu razdelka 6.2 je 2048 pomotoma ponovljen; nadaljnje besedilo in tabela 9 jasno obravnavata 4096.

Razdelek 6.3, enačba (14), uporablja aditivno predpostavko `QBER = 0,25p + QBER_SN`. Ta ni enaka našemu zaporednemu depolarizacijskemu kanalu, kjer je dodatek `(1 − λ)r/4`. Članek motivira ločeno upoštevanje šuma in prestrezanja, ne upravičuje samodejnega prenosa njihovih dolžin v naše kontrolne vzorce ali njihovega modela v naš simulator.

## Lee, Lee in Lee (2023)

*Analysis on Eavesdropper Detection in BB84 Quantum Key Distribution Protocol against Partial Intercept-and-resend Attack.* ONDM 2023. [PDF](https://dl.ifip.org/db/conf/ondm/ondm2023/1570879964.pdf).

Razdelka II–III opredelita FPR/FNR in neodvisne Bernoullijeve napake. Avtorji nato QBER približajo z normalno porazdelitvijo in izberejo prag z minimizacijo `FPR + FNR`, enačba (13). Ne izvajajo našega eksaktnega enostranskega binomskega testa pri fiksnem α. Enačba (9) je `μ_eve = 0,25ρ + μ_ch − ρ μ_ch²`; izhaja iz njihovega modela kanalov Alice–Eve in Eve–Bob ter ni naša enačba.

Sliki 1–3 in razdelek IV vključujejo kontrolne vzorce 100, 300 in 500 ter osnovne QBER 3 %, 5 %, 7 % oziroma primerjave do približno 9 %. To daje neposredno motivacijo delu naše mreže in H1/H2, ne potrjuje celotne mreže ali α = 0,05.

## Naše odločitve

- Kontrolni vzorci 20, 50 in 1000 razširijo raziskovalni razpon; 100, 300 in 500 imajo neposredne primerjave pri Lee idr. Nabor ni replika enega članka.
- λ = 0,06–0,50, vsi naši deleži prestrezanja, N = 2400 in 30/2000 ponovitev so raziskovalne nastavitve. Visoki QBER so stresni scenariji zaznavanja.
- Eksaktni binomski test je primeren za naš model neodvisnih napak in se izogne normalnemu približku pri m = 20 ali majhnem pričakovanem številu napak. Je združljiv z Bernoullijevo izhodiščno analizo, ni pa Leejev postopek.
- α = 0,05 vnaprej omeji lažne alarme pri posameznem testu. [NIST](https://www.itl.nist.gov/div898/handbook/prc/section1/prc131.htm) navaja 0,10, 0,05 in 0,01 kot običajne statistične izbire. To je utemeljitev konvencije in našega kompromisa, ne dokaz ustreznosti za kriptografsko varnost. V pregledanih delih treh člankov ni potrditve uporabe natanko našega α. Smiselna nadaljnja analiza je občutljivost na α in negotovost osnovnega QBER.

## Dokumentacija orodij

- [Aer — depolarizing_error](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.depolarizing_error.html): definicija kanala in λ.
- [AerSimulator](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator.html): izvajanje in semena.
- [SciPy — binomtest](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html): enostranski test in intervali.
- [SciPy — proportion_ci](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats._result_classes.BinomTestResult.proportion_ci.html): Wilsonov interval.
