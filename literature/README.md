# Literatura za raziskavo BB84

Brezplačni viri, izbrani za seminarsko nalogo **Vpliv šuma in velikosti kontrolnega vzorca na zaznavanje prisluškovanja v protokolu BB84**.

## Prednostni vrstni red branja

1. **Gisin et al., Quantum cryptography (2002)** — izberi razdelke o BB84, prisluškovanju in varnosti. [PDF](https://arxiv.org/pdf/quant-ph/0101098)
2. **Bennett & Brassard, Quantum cryptography: Public key distribution and coin tossing (1984)** — originalni protokol. [PDF](https://arxiv.org/pdf/2003.06557)
3. **Cai & Scarani, Finite-key analysis for practical implementations of quantum key distribution (2009)** — finite-size statistika in vpliv omejenega vzorca. [PDF](https://arxiv.org/pdf/0811.2628)
4. **Tomamichel et al., Tight finite-key analysis for quantum cryptography (2012)** — natančnejše varnostne meje za končne ključe. [PDF](https://arxiv.org/pdf/1103.4130)
5. **Scarani et al., The security of practical quantum key distribution (2009)** — fizikalne omejitve in šum. [PDF](https://arxiv.org/pdf/0802.4155)
6. **Fiorini et al., Estimating Interception Density in the BB84 Protocol: A Study with a Noisy Quantum Simulator (2024)** — **zelo neposredno povezan članek**: parcialni napad, šum, velikost podatkov in sklepanje; metodologijo uporabi kot primerjavo, ne kot predlogo za prepis. [PDF](https://www.mdpi.com/1999-5903/16/8/275/pdf)
7. **Shor & Preskill, Simple Proof of Security of the BB84 Quantum Key Distribution Protocol (2000)** — neobvezno za širšo razpravo o varnostnih dokazih. [PDF](https://arxiv.org/pdf/quant-ph/0003004)

Prenos na lokalni disk:

```bash
python scripts/fetch_literature.py
```

Skripta preveri format datoteke in neuspele prenose jasno označi. Povezave so zapisane v `sources.json`, citati pa v `references.bib`.

**Povezava z eksperimentom:** članka Cai–Scarani in Tomamichel idr. utemeljujeta pomen končne velikosti podatkov v QKD; ne predstavljata pa dokaza, da je naš preprosti binomski detektor napadov kriptografsko varen.

**Letnice in metapodatki:** originalni članek Bennett–Brassard je iz leta **1984**; leto 2020 označuje samo nalaganje skena na arXiv. Gisin idr. je revijalna objava iz **2002**, čeprav je prednatis na arXiv iz 2001. Identifikatorji prednatisov niso letnice revijalnih objav. Obstoječa `sources.json` in `references.bib` ohranjata identifikatorje ter bibliografske podatke priložene zbirke.

Pri preverjanju izvirnega PDF-ja Fiorini idr. je bilo popravljeno ime četrtega avtorja: **Antonio Osele**, ne Alberto Osele. DOI, naslov, letnica in identifikatorji drugih virov so ohranjeni.

Študija Fiorini idr. je primerjalna literatura za šumno prestrezanje in ocenjevanje gostote prestrezanja. Naš odobreni načrt posebej preučuje velikost javno preverjenega vzorca in zaznavanje ob določenem cilju FPR; rezultatov ali varnostnih trditev članka ne prenašamo samodejno na svoj model. Če MDPI zavrne prenos, uporabimo [stran založnika](https://www.mdpi.com/1999-5903/16/8/275) ali [institucionalni repozitorij](https://arpi.unipi.it/handle/11568/1271727). Za ta članek ni navedenega identifikatorja arXiv.

Skripta deluje iz poljubne delovne mape in uporablja samo Pythonovo standardno knjižnico. Preveri HTTP odgovor, dolžino, glavo `%PDF-` in končno oznako `%%EOF`, zavrne HTML in prenos shrani atomsko. To je osnovno preverjanje oblike, ne celovita analiza strukture PDF. Veljavne obstoječe datoteke preskoči; začasne omrežne napake ponovi enkrat. Ob neuspehu izpiše ročne povezave in vrne izhodno kodo 1. PDF-ji ostajajo lokalni in so prezrti v Gitu.

## Uradna dokumentacija

- [Qiskit Aer – AerSimulator](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator.html)
- [Qiskit Aer – depolarizing_error](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.depolarizing_error.html)
- [SciPy – binomtest](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html)

## Preverjanje prenosa (2. 11. 2026)

Vseh sedem PDF-jev je bilo dejansko prenesenih z navedenih naslovov. Vsi so prestali preverjanje skripte in jih `pdfinfo` odpre (6, 57, 52, 17, 16, 22 in 5 strani v vrstnem redu manifesta). Pri skenu Bennett–Brassard `pdfinfo` izpiše opozorilo o nepopolnem seznamu izbirnih slojev, vendar vrne uspeh in prepozna vseh šest strani. Ponovni zagon prenosnika preskoči vseh sedem datotek. To je preverjanje zbirke literature, ne rezultat raziskovalnega eksperimenta.
