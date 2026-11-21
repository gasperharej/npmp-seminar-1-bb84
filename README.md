# Vpliv šuma in velikosti kontrolnega vzorca na zaznavanje prisluškovanja v protokolu BB84

Magistrska seminarska naloga pri predmetu Nekonvencionalne platforme in metode procesiranja (NPMP), UL FRI.

**Raziskovalno vprašanje:** Kako stopnja kvantnega šuma in velikost kontrolnega vzorca vplivata na verjetnost pravilnega zaznavanja prisluškovanja v protokolu BB84?

## Trenutno stanje

Implementirani so simulator Python/Qiskit Aer, delni napad intercept-resend, depolarizacijski kanal, uskladitev baz, kontrolni vzorci, eksaktni binomski detektor, eksperimenti H1/H2, povzetki z intervali zaupanja in grafi. Projekt obravnava hipotezi H1 in H2.

Ob pregledu 8. 11. 2026 je lokalna mapa `src/bb84/results/` vsebovala 50.000 poskusov (25 konfiguracij × 2000 ponovitev), 150 povzetkov in tri grafe. Preverjeni so bili izračuni vseh povzetkov in ponovitve 50 semen (po dve na konfiguracijo); celoten eksperiment ni bil ponovno izveden. Rezultati so prezrti v Gitu in pri svežem kloniranju niso zagotovljeni. Obstoječi CSV ne beleži različic knjižnic ali revizije kode, zato njegov izvor ni v celoti dokumentiran.

## Model in hipoteze

Alice pripravi `|0⟩`, `|1⟩`, `|+⟩` ali `|−⟩` (vrata X za bit 1, nato H za bazo X). Eve vsak signal neodvisno prestreže z verjetnostjo `r = interception_rate`, ga izmeri v naključni bazi Z/X in pošlje stanje po kolapsu. Po meritvi v X se z dodatnim H vrne v ustrezno stanje te baze. Bob za meritev v X uporabi H pred meritvijo v Z. Njegov izid je klasični bit `c[0]`, skrajno desno v Qiskitovem izpisu `c[1]c[0]`.

Na edina vrata `id`, **po Eve in pred Bobovim merilnim zasukom**, je vezan kanal

```text
E(ρ) = (1 − λ)ρ + λ I/2
q0 = λ/2                          # QBER brez Eve
q1 = λ/2 + (1 − λ)r/4             # QBER z Eve po uskladitvi baz
```

`noise_level` pomeni λ, ne verjetnosti bitnega obrata. Priprava in meritve so idealne. Brez šuma je pri polnem prestrezanju pričakovani QBER 25 %. Simulator in model šuma se ustvarita enkrat na ponovitev ter uporabita za vseh 2400 signalov. Vezja se neposredno podajo Aeru brez zunanjega `transpile`; dodajanje optimizacije zahteva preverjanje, da ne odstrani `id`. Nizkonivojski `transmit` uporablja šum podanega simulatorja; šum nastavimo prek `run_bb84`.

Obdržimo samo prenose z ujemajočima se bazama Alice in Boba. Iz njih brez ponavljanja izžrebamo urejen vzorec 1000 bitov; njegovih prvih `m` bitov tvori posamezen kontrolni vzorec. Šest velikosti je tako gnezdenih in medsebojno odvisnih. To so alternativne analize iste ponovitve, ne šest neodvisnih eksperimentov. Eksperiment ne izdeluje končnega ključa; kontrolni biti so javno razkriti.

- **H1:** Pri fiksnem šumu večji vzorec praviloma izboljša verjetnost zaznave ob umerjenem kriteriju. Diskretni prag lahko povzroči lokalne padce moči; stroga monotonost ni zagotovljena.
- **H2:** Pri fiksnih velikosti vzorca in deležu prestrezanja večji šum praviloma oteži razlikovanje: razlika `q1 − q0 = (1 − λ)r/4` se manjša. Zaradi diskretnega praga stroga monotonost TPR ni zagotovljena. Primerjamo TPR ob spremljanju dejansko doseženega FPR.

### Statistično odločanje

Za `k` napak v `m` bitih je `QBER = k/m`. Ob ničelni hipotezi velja `K ~ Bin(m, q0)`; enostranska alternativa je QBER > q0. Uporabimo `scipy.stats.binomtest(..., alternative="greater")` in sprožimo alarm pri **pvalue ≤ α**. Kritični prag je najmanjši c s `P_q0(K ≥ c) ≤ α`; teoretična moč je `P_q1(K ≥ c)`.

`α = 0,05` je vnaprej izbrana dovoljena verjetnost lažnega alarma za **en test**. Je uveljavljena statistična konvencija ([NIST](https://www.itl.nist.gov/div898/handbook/prc/section1/prc131.htm)) in naša raziskovalna izbira, ne varnostni standard BB84 niti potrjena nastavitev treh izbranih člankov. Eksaktni diskretni test je praviloma konservativen: na raziskovalni mreži je teoretični FPR približno 1,59–4,96 %, ne vedno 5 %. Pravilo »alarm, če zazna katerikoli od šestih testov« tu ni umerjeno na skupnih 5 %.

TPR je delež alarmov pri `r > 0`, FPR pri `r = 0`, FNR pa `1 − TPR`. CSV neposredno shranjuje TPR/FPR v skupnem stolpcu `observed_rate`; FNR izpeljemo. `ci_low`/`ci_high` sta točkovna dvostranska 95-% **Wilsonova** intervala za delež alarmov med neodvisnimi ponovitvami; nista eksaktna intervala niti intervala za QBER. Pri 2000 ponovitvah je največja standardna napaka deleža približno 1,12 odstotne točke; 30 ponovitev je le preizkus poteka.

Binomski model velja za neodvisne, enako porazdeljene napake tega simulatorja in znani `q0`. Vzorčenje brez ponavljanja iz naključno ustvarjenih neodvisnih bitov ohrani binomsko marginalno porazdelitev; pogojno na že fiksno število napak celotnega prenosa bi bila porazdelitev hipergeometrična. Negotovost kalibracije `q0`, časovno odvisni šum in korelirani napadi niso obravnavani.

## Raziskovalne nastavitve

| Parameter | Vrednosti |
|---|---|
| Kontrolni vzorec m | 20, 50, 100, 300, 500, 1000 |
| Depolarizacija λ | 0,06; 0,10; 0,20; 0,40; 0,50 |
| Osnovni QBER q0 | 3 %, 5 %, 10 %, 20 %, 25 % |
| Prestrezanje r | 0 %, 10 %, 20 %, 50 %, 100 % |
| Signali na ponovitev N | 2400 |
| Stopnja značilnosti α | 0,05 |
| Ponovitve na (λ, r) | preizkus 30; končno 2000 |
| Osnovno seme | 20261107 |

Če ostane manj kot 1000 bitov, se ponovitev ustavi z napako; ne preskakuje se tiho in se ne izbira manjšega vzorca. Pri N = 2400 in poštenih bazah je verjetnost tega dogodka približno `1,16 × 10⁻¹⁶`.

## Struktura

```text
src/bb84/
  protocol.py             priprava, Eve, kanal, Bob, uskladitev baz
  analysis.py             QBER, vzorčenje, detektor, kritični prag
  experiments.py          H1/H2, CSV, povzetki, grafi, CLI
  results/                obstoječi lokalni raziskovalni izhodi (prezrti)
tests/                    testi protokola, statistike in eksperimentov
scripts/bootstrap.sh      razvojno okolje
scripts/fetch_literature.py
literature/               manifest, BibTeX, napotki; pdfs/ je prezrt
pyproject.toml            paket in konfiguracija Pytest/Ruff
uv.lock                   zaklenjene odvisnosti po različicah Pythona
requirements.lock         izvoz uv.lock z različicami in zgoščenimi vrednostmi
```

`bb84-seminar-files.zip` je začetni arhiv, ne aktualna izvorna koda. `.gitignore` izloča okolja, predpomnilnike, lokalne PDF-je, rezultate in grafe. `.env.example` vsebuje stare zgledne spremenljivke `BB84_*`; simulator jih ne bere. `.envrc` samo doda `.venv/bin` v PATH in ne namešča paketov ali nalaga `.env`.

## Namestitev in preverjanje

Iz korena repozitorija na Linuxu z Bash/Zsh:

```bash
./scripts/bootstrap.sh
source .venv/bin/activate
export MPLCONFIGDIR="$PWD/.cache/matplotlib"
python -m pytest -q
python -m ruff check .
```

Skripta ustvari `.venv`, če je še ni, namesti `requirements.lock` z obveznimi hashi ter paket v editable načinu (`--no-deps --no-build-isolation -e .`), preveri odvisnosti in uvoze. Potrebuje Bash, Python z `venv`/`pip` in internet. Prednostno išče Python 3.14, nato 3.13, 3.12, 3.11; izbira za **novo** okolje je npr. `BB84_PYTHON=python3.14 ./scripts/bootstrap.sh`. Obstoječega interpreterja ne zamenja.

`pyproject.toml` dovoljuje Python 3.11–3.14. V tem pregledu so bili izvedba in testi preverjeni na **Linux x86_64, CPython 3.14.4, Qiskit 2.6.2, Aer 0.18.2**. Druge različice in operacijski sistemi niso izvedbeno preverjeni; lock vsebuje ločene odvisnosti za Python 3.11. Priporočena je preverjena različica 3.14.

Bootstrap je bil uspešno preverjen v obstoječi `.venv`, vključno z editable namestitvijo in `pip check`. Poskus čiste namestitve v novo okolje `/tmp` se je ustavil pri prenosih paketov (timeout in nato napaka DNS); namestitev od začetka zato v tem pregledu ni v celoti potrjena. Integracija direnv z interaktivno lupino ni bila preizkušena.

`uv` ni potreben za bootstrap. Razvijalci izvoz obstoječega zaklepa obnovimo z:

```bash
uv export --locked --extra dev --no-emit-project --output-file requirements.lock
```

Nadgradnjo odvisnosti izvajamo ločeno in nato ponovno preverimo model ter semena. Neobvezni `direnv allow .` po pregledu `.envrc` omogoči samodejno aktivacijo že ustvarjenega okolja.

## Zagon

Ukaze izvajamo iz **korena repozitorija**. Kratek preizkus celotne mreže (25 poskusov):

```bash
python -m bb84.experiments --repetitions 1 --workers 2 --output-dir /tmp/bb84-smoke
```

Načrtovani preizkus s 30 ponovitvami na konfiguracijo (750 poskusov):

```bash
python -m bb84.experiments --repetitions 30 --workers 2 --output-dir results/test-30
```

Končni zagon je `python -m bb84.experiments --repetitions 2000 --output-dir results/final`. Tudi ukaz **brez argumentov** privzeto izvede 2000 ponovitev za vsako konfiguracijo (50.000 poskusov, 120 milijonov signalov); lahko traja dolgo. Za pomoč uporabimo `python -m bb84.experiments --help`.

Ponovni zagon istega ukaza dopolni manjkajoče poskuse. Za podaljšanje preizkusa povečamo `--repetitions` v isti izhodni mapi. Za neodvisen ponovni eksperiment izberemo novo mapo. Vsako ponovitev določa seme `BASE_SEED + indeks_λ × 10.000.000 + indeks_r × 100.000 + trial`; seje imajo ločena semena, vsak proces pa pred ponovitvijo ponastavi Pythonov generator. Tudi Aer za vsak signal dobi seme iz tega generatorja. Število procesov in vrstni red opravil ne spremenita rezultatov v preverjenem okolju. Privzeto so največ štirje procesi; Aer uporablja eno nit na proces. Bitna ponovljivost med različicami knjižnic ni zagotovljena.

CSV pred nadaljevanjem preveri stolpce, N, α, semena, podvojitve, napake in odločitve. Celotne vrstice sproti izprazni v datoteko. Ob odrezani ali neskladni vrstici se ustavi in datoteke ne popravlja samodejno: pregledamo kopijo in manjkajoč poskus nato ponovno izračunamo z istim semenom. Hkratna zapisovalca v isti CSV in izguba podatkov ob odpovedi diska nista podprta. Za arhiviranje shranimo tudi revizijo kode, različice paketov in ukaz zagona.

### Izhodi

Vse datoteke se ustvarijo v `--output-dir` (privzeto `results/`, glede na trenutni delovni imenik):

| Datoteka | Vsebina |
|---|---|
| `h1_h2_trials.csv` | ena vrstica na ponovitev: λ, r, trial, seed, N, α, število obdržanih bitov, `errors_m` in `detected_m` za vseh šest m |
| `h1_h2_summary.csv` | ena vrstica na (λ, r, m): ponovitve, alarmi, TPR/FPR, Wilsonov IZ, teoretična verjetnost in povprečni QBER vzorca |
| `h1_tpr_vs_sample.png` | TPR glede na m pri r = 20 % |
| `h2_tpr_vs_noise.png` | TPR glede na osnovni QBER pri m = 300 |
| `fpr_vs_sample.png` | FPR brez Eve glede na m ter nominalni α |

Novi grafi H1/H2/FPR prikažejo točkovne 95-% intervale in črtkano teorijo. Obstoječi lokalni grafi so iz starejše različice in teh dodatkov nimajo. Povzetki uporabljajo vse veljavne shranjene ponovitve, tudi če mreža še ni zaključena: preverimo stolpec `repetitions`.

`--summarize-only --output-dir <mapa>` obstoječi CSV ponovno analizira brez kvantnih simulacij, vendar **prepiše izpeljane povzetke in grafe v tej mapi**. Za ohranitev raziskovalnih izhodov najprej prekopiramo `h1_h2_trials.csv` v novo mapo in analiziramo kopijo.

### Končni grafi za poročilo

Iz popolnega lokalnega nabora 50.000 poskusov pripravimo tri grafe H1, H2 in FPR brez novih simulacij:

```bash
MPLCONFIGDIR=.cache/matplotlib python scripts/prepare_final_figures.py
```

Skripta privzeto prebere `src/bb84/results/h1_h2_trials.csv` in ustvari **novo** mapo `results/final-figures/`. Preveri vseh 25 konfiguracij in 2000 ponovitev na konfiguracijo; nepopolnega preizkusnega CSV ne uporabi za končne grafe. Obstoječe izhodne mape ne prepiše; za ponoven izvoz določimo npr. `--output-dir results/final-figures-v2`.

Vsaka slika je na voljo kot PNG (300 dpi), vektorski PDF in SVG. Grafa H1/FPR imata logaritemsko os velikosti vzorca z vsemi šestimi oznakami. Priloženi so kopija izvornega CSV, povzetek H1/H2, opisi slik v `README.md`, posnetek uporabljene kode in `provenance.json` z različicami okolja priprave grafov ter SHA-256. Zgodovinskih različic prvotne simulacije iz CSV ni mogoče obnoviti. Celotna mapa je prezrta v Gitu, zato jo arhiviramo ločeno.

## Omejitve in literatura

Alarm pomeni odstopanje od znanega modela šuma, ne dokaz Eve ali varnosti ključa. Projekt ne izvaja popravljanja napak, ojačanja zasebnosti, avtentikacije klasičnega kanala ali dokaza varnosti končnega ključa. Visoki QBER 20–25 % so raziskovalni stresni scenariji zaznavanja in ne potrjujejo uporabne varne izmenjave ključa.

- [Mina in Simion (2020)](https://eprint.iacr.org/2020/1074): simulacija BB84 in intercept-resend v Qiskitu, idealni primer zaznavanja ob napaki.
- [Fiorini idr. (2024)](https://doi.org/10.3390/fi16080275): ocenjevanje gostote prestrezanja s šumnim simulatorjem; njihov model šuma in velikosti ključev niso naši kontrolni vzorci.
- [Lee, Lee in Lee (2023)](https://dl.ifip.org/db/conf/ondm/ondm2023/1570879964.pdf): povezava med vzorcem, šumom, FPR/FNR in pragom; uporabljajo normalni približek in minimizacijo FPR + FNR, ne našega testa pri fiksnem α.

Celotna mreža parametrov, α, N in število ponovitev so naše metodološke odločitve. Razmejitev od dejanskih metod člankov je v [literature/README.md](literature/README.md), citati v [references.bib](literature/references.bib). PDF-je pridobimo s `python scripts/fetch_literature.py`; ob nedostopnosti strežnika skripta vrne napako in navede ročno povezavo. Ob pregledu so bili vsi trije PDF-ji dostopni in prebrani.

## Razvojni načrt

- [x] BB84, delni intercept-resend, kanal, uskladitev baz in vzorčenje.
- [x] Eksaktni detektor, TPR/FPR, intervali, teorija in lokalni podatki H1/H2.
- [x] Testi ključnih funkcij, kratke simulacije, paralelna ponovljivost in nadaljevanje.
- [x] Pripraviti končne grafe na kopiji in arhiv z okoljem priprave ter posnetkom kode; zgodovinsko okolje simulacij ostaja nezabeleženo.
- [ ] Neobvezna nadgradnja: oceniti negotovost kalibracije q0.
- [ ] Oblikovati zaključke H1/H2 z upoštevanjem odvisnih vzorcev in diskretnosti.
- [ ] Napisati seminarsko poročilo z omejitvami modela in primerjavo literature.

## Pisanje poročila v LaTeXu (skupina 22)

Prilagojena predloga je v `report/`. Besedilo pišemo v
`report/Skupina22/main.tex`, skupni viri so v `report/references.bib`,
slike PDF pa v `report/Skupina22/img/`. Osnutek vsebuje navodila `DOPOLNI`,
ki jih pred oddajo zamenjamo z lastnim končnim besedilom. Vse nove oznake
in ključi virov imajo predpono `g22:`. Lokalni `editor.tex` prevede samo
naše poglavje z izvirnim razredom `svmult`; navodila in zgledi iz predloge
so ohranjeni, vendar niso vključeni v lokalni PDF.

Na Linuxu x86_64 lokalni TinyTeX namestimo brez `sudo` z:

```bash
bash scripts/setup_latex.sh
bash scripts/build_report.sh
```

Namestitev potrebuje internet, `curl`, `tar`, `xz` in `perl`. Orodja in
paketi so v prezrti mapi `.tools/.TinyTeX`; ne spreminjamo profila lupine.
Predloga uporablja pdfLaTeX, BibTeX in latexmk. Za prevod po namestitvi
internet ni potreben. PDF in pomožne datoteke so v `report/build/`.
Za neprekinjen prevod uporabimo `bash scripts/build_report.sh -pvc -view=none`.
V VS Code je predvidena razširitev LaTeX Workshop; nastavljen je prevod
ob shranjevanju ter ogled PDF v zavihku. Ročni prevod: Ctrl+Alt+B;
ogled: Ctrl+Alt+V. Odprta mora biti korenska mapa celotnega projekta.

Dodatna dokazila za zahteve QC obnovimo z:

```bash
MPLCONFIGDIR=.cache/matplotlib .venv/bin/python scripts/prepare_report_checks.py
```

Skripta **prepiše samo svoje izhode v `report/evidence/`**. Izvede devet
kratkih kontrolnih simulacij (po ena seja s 6000 signali), izmeri vezja
pred in po dodatnem prevajanju ter shrani dejanski neuspešen poskus:
optimizaciji 1 in 3 odstranita `id` in s tem šumni kanal. Glavni
eksperiment H1/H2 ostane nespremenjen in ne uporablja zunanjega `transpile`.
Izpeljane tabele LaTeX se samodejno vključijo v osnutek. Različice okolja
teh novih preverjanj so shranjene posebej od zgodovinskih podatkov H1/H2.
V `report/evidence/` je tudi kopija popolnega povzetka H1/H2;
`main_results_provenance.json` beleži izvor in hashe prenesenih grafov
ter tabel. Skripta teh zgodovinskih povzetkov ne prepisuje.

Po navodilih oddamo približno desetstransko poglavje, izvor LaTeX, PDF,
prosojnice in povezavo do repozitorija. Rok v priloženih navodilih je
22. 11. 2026; predstavitev traja približno deset minut. Obvezni so tudi
razdelek »Kaj ni delovalo«, dejanski doprinosi avtorjev in izjava o uporabi UI.
