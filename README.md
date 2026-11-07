# Vpliv šuma in velikosti kontrolnega vzorca na zaznavanje prisluškovanja v protokolu BB84

Magistrska seminarska naloga pri predmetu Nekonvencionalne platforme in metode procesiranja (NPMP), UL FRI.

## O projektu

BB84 je protokol za kvantno distribucijo ključev. Alice pošilja kvantna stanja Bobu, Eve pa jih lahko prestreže, izmeri in pošlje naprej. Takšno prisluškovanje lahko povzroči napake, vendar napake nastanejo tudi zaradi šuma v kanalu.

V projektu bomo sami postopoma implementirali BB84 v Pythonu s Qiskitom. Raziskali bomo, kako šum in število javno preverjenih bitov vplivata na zanesljivost zaznavanja prisluškovanja.

## Raziskovalni cilj

**Kako stopnja kvantnega šuma in velikost kontrolnega vzorca vplivata na verjetnost pravilnega zaznavanja prisluškovanja v protokolu BB84?**

Cilj je primerjati zaznavanje pri različnih stopnjah šuma in velikostih vzorca, pri tem pa spremljati tudi lažne alarme. Preverili bomo tri hipoteze:

- **H1:** Pri enaki stopnji šuma večji kontrolni vzorec praviloma izboljša verjetnost zaznave napada, če je kriterij odločanja ustrezno umerjen.
- **H2:** Večji šum oteži razlikovanje med legitimnim prenosom in prisluškovanjem, saj povzroča napake tudi brez napadalca.
- **H3:** Za določeno dovoljeno stopnjo lažnih alarmov je mogoče oceniti minimalno velikost kontrolnega vzorca, potrebno za želeno verjetnost zaznave v izbranem modelu napada.

## Kako bo delovala simulacija

1. Alice naključno izbere bite in baze ter pripravi ustrezna kvantna stanja.
2. Stanja pošlje po kvantnem kanalu proti Bobu.
3. Eve lahko prestreže del stanj, jih izmeri in ponovno pošlje (*intercept-resend*).
4. Kanal lahko po tem koraku vnese nastavljiv šum, tudi kadar Eve ni prisotna.
5. Bob izbere svoje baze in izmeri prejeta stanja.
6. Alice in Bob javno primerjata uporabljene baze ter obdržita le bite z ujemajočima se bazama.
7. Iz ohranjenih bitov naključno izbereta kontrolni vzorec, javno primerjata vrednosti in te bite izločita iz preostanka.
8. Izračunata QBER: delež napačnih bitov v kontrolnem vzorcu.
9. Vnaprej določeno statistično pravilo presodi, ali so napake sumljive glede na pričakovani šum brez Eve.

Velikost kontrolnega vzorca pomeni število preverjenih bitov po primerjavi baz, ne vseh poslanih signalov. Šum lahko povzroči napake tudi brez Eve, zato opažene napake same po sebi niso dokaz prisluškovanja. Preostali biti še niso končni varni ključ.

## Načrtovani eksperimenti

- **Eksperiment 1 — Osnovno preverjanje BB84:** v idealnem kanalu brez Eve pričakujemo prenos brez napak; pri polnem napadu intercept-resend brez šuma približno 25 % QBER med biti z ujemajočima se bazama.
- **Eksperiment 2 — Vpliv šuma:** pri različnih stopnjah šuma primerjamo komunikacijo z Eve in brez nje.
- **Eksperiment 3 — Velikost kontrolnega vzorca:** primerjamo različna števila preverjenih bitov ter njihov vpliv na zaznavanje in lažne alarme. Pravilo odločanja umerimo na izbrano dovoljeno stopnjo lažnih alarmov.

Vsako nastavitev bomo večkrat ponovili, beležili parametre in semena naključnosti ter rezultate primerjali s preprostimi teoretičnimi pričakovanji. Spremljali bomo:

- **QBER:** delež napak v javno preverjenih bitih.
- **TPR:** delež poskusov z Eve, pri katerih napad zaznamo.
- **FPR:** delež poskusov brez Eve, pri katerih sprožimo lažni alarm.
- **FNR:** delež poskusov z Eve, pri katerih napad spregledamo.

## Tehnologije

- Python v navideznem okolju `.venv`; Qiskit in Qiskit Aer za kvantne simulacije.
- NumPy, SciPy, Pandas in Matplotlib za obdelavo podatkov, statistiko in grafe.
- Pytest za teste in Ruff za preverjanje kode.
- Neobvezno direnv za samodejno aktivacijo okolja.

## Namestitev

Repozitorij kloniramo in vstopimo v njegovo mapo. V spodnjem zgledu zamenjamo URL in ime mape:

```bash
git clone "<repository-url>"
cd "<repository-directory>"
```

Projekt podpira **Python 3.11–3.14**, priporočena je različica 3.14. Potrebujemo Python z moduloma `venv` in `pip`, dostop do interneta ter Bash za zagonsko skripto:

```bash
./scripts/bootstrap.sh
```

Skripta po potrebi ustvari `.venv`, namesti pakete iz `requirements.lock`, pripravi paket `bb84` za razvoj v urejevalnem načinu in preveri uvoze. Ponovni zagon ohrani obstoječe okolje. Zagonska skripta zahteva Bash; drugih lupin zanjo ne predpostavljamo.

Pri ustvarjanju okolja skripta najprej poišče Python 3.14, nato starejše podprte različice. Interpreter lahko izberemo izrecno:

```bash
BB84_PYTHON=python3.14 ./scripts/bootstrap.sh
```

Če `.venv` že obstaja in želimo preiti na Python 3.14, staro okolje najprej preimenujemo (npr. `mv .venv .venv-backup`) in ponovno zaženemo zgornji ukaz.

### Posodobitev odvisnosti

`requirements.lock` določa preverjene različice in njihove zgoščene vrednosti. Z nameščenim orodjem [uv](https://docs.astral.sh/uv/) ga posodobimo na najnovejše združljive stabilne izdaje za podprte različice Pythona:

```bash
uv pip compile pyproject.toml --extra dev --universal --upgrade --generate-hashes --only-binary :all: --no-emit-package bb84-seminar --output-file requirements.lock
./scripts/bootstrap.sh
```

## Aktivacija okolja

Na Linuxu ali macOS z Bash ali Zsh okolje ročno aktiviramo z:

```bash
source .venv/bin/activate
```

Če že uporabljamo direnv, povezan z našo lupino, lahko po pregledu `.envrc` namesto ročne aktivacije enkrat dovolimo:

```bash
direnv allow .
```

Ob vstopu v mapo direnv nastavi `VIRTUAL_ENV` in doda `.venv/bin` na začetek `PATH`; ob odhodu obnovi prejšnje okolje. `.venv` mora biti prej ustvarjena. Vstop v mapo ne namešča odvisnosti.

## Uporaba in razvoj

Trenutno je pripravljeno razvojno okolje s praznim paketom `bb84`. Simulator, testi in eksperimenti še niso implementirani; raziskovalnih rezultatov še ni.

Po aktivaciji okolja preverimo namestitev in kodo:

```bash
python -c "import qiskit; import qiskit_aer; print('Qiskit je pripravljen')"
python -m ruff check .
```

Ko napišemo lastne teste, jih zaženemo z `python -m pytest`. Dokler jih ni, Pytest sporoči `no tests ran` in vrne kodo 5; to ni uspešno opravljen nabor testov.

## Literatura

Uporabljamo tri praktično usmerjena dela:

1. **Mina in Simion (2020), *A Scalable Simulation of the BB84 Protocol Involving Eavesdropping*.** Razlaga BB84, napada intercept-resend in simulacije v Qiskitu. [PDF — arhivska kopija](https://web.archive.org/web/20240901000000id_/https://eprint.iacr.org/2020/1074.pdf)
2. **Fiorini idr. (2024), *Estimating Interception Density in the BB84 Protocol: A Study with a Noisy Quantum Simulator*.** Primerjava simulacij s šumom in prestrezanjem. [PDF](https://www.mdpi.com/1999-5903/16/8/275/pdf)
3. **Lee, Lee in Lee (2023), *Analysis on Eavesdropper Detection in BB84 Quantum Key Distribution Protocol against Partial Intercept-and-resend Attack*.** Kontrolni vzorec, prag zaznavanja ter lažni alarmi in spregledani napadi. [PDF](https://dl.ifip.org/db/conf/ondm/ondm2023/1570879964.pdf)

Izbrane PDF-je prenesemo v lokalno mapo `literature/pdfs/`:

```bash
python scripts/fetch_literature.py
```

Skripta preveri datoteke in preskoči že prenesene veljavne PDF-je. Ti so prezrti v Gitu. Napotki za branje so v [literature/README.md](literature/README.md), citati pa v [literature/references.bib](literature/references.bib).

## Razvojni načrt

- [ ] Razumeti BB84 in njegova štiri kvantna stanja.
- [ ] Implementirati osnovno pripravo stanj in meritve.
- [ ] Implementirati Alice in Boba.
- [ ] Implementirati primerjavo baz in izločanje bitov z neujemajočimi se bazami.
- [ ] Implementirati napad intercept-resend.
- [ ] Implementirati šum kvantnega kanala.
- [ ] Implementirati izbiro kontrolnega vzorca in QBER.
- [ ] Implementirati zaznavanje prisluškovanja in metrike.
- [ ] Izvesti eksperimente in pripraviti grafe.
- [ ] Primerjati rezultate s teoretičnimi pričakovanji.
- [ ] Napisati seminarsko poročilo.
