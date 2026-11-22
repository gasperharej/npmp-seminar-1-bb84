# Vpliv šuma in velikosti kontrolnega vzorca na zaznavanje prisluškovanja v protokolu BB84

Seminarska naloga pri predmetu **Nekonvencionalne platforme in metode procesiranja (NPMP)** na Univerzi v Ljubljani, Fakulteti za računalništvo in informatiko.

**Avtor:** Gašper Harej

## O projektu

Projekt raziskuje, kako depolarizacijski šum in velikost kontrolnega vzorca vplivata na zaznavanje prisluškovanja v protokolu za kvantno distribucijo ključev **BB84**. V Pythonu in knjižnici **Qiskit Aer** simuliramo prenos kvbitov, napad s prestrezanjem in ponovnim pošiljanjem (*intercept-resend*) ter šumni kvantni kanal.

Preverjamo dve hipotezi:

- **H1:** Pri enakem šumu in deležu prestrezanja večji kontrolni vzorec praviloma omogoča uspešnejše zaznavanje.
- **H2:** Pri enaki velikosti kontrolnega vzorca in deležu prestrezanja večji šum praviloma otežuje zaznavanje.

Prisluškovanje zaznavamo z **enostranskim eksaktnim binomskim testom** pri stopnji značilnosti `α = 0,05`. Uspešnost ocenjujemo z deležema pravilnih zaznav (**TPR**) in lažnih alarmov (**FPR**).

## Model in eksperimenti

Alice in Bob za vsak kvbit neodvisno izbereta računsko (`Z`) ali diagonalno (`X`) bazo. Eve vsak kvbit prestreže z verjetnostjo `r` in ga izmeri v naključno izbrani bazi. Po uskladitvi baz ohranimo samo ustrezne bite.

Šum predstavimo z depolarizacijskim kanalom:

```text
D_λ(ρ) = (1 − λ)ρ + λ I/2
q₀ = λ/2                       # pričakovani QBER brez Eve
q₁ = λ/2 + (1 − λ)r/4          # pričakovani QBER ob prisotnosti Eve
```

| Parameter | Vrednosti |
|---|---|
| Poslani kvbiti na ponovitev | `N = 2400` |
| Depolarizacijski šum `λ` | `0,06; 0,10; 0,20; 0,40; 0,50` |
| Verjetnost prestrezanja `r` | `0; 0,10; 0,20; 0,50; 1` |
| Velikosti kontrolnega vzorca `m` | `20, 50, 100, 300, 500, 1000` |
| Ponovitve na kombinacijo `(λ, r)` | `2000` |
| Stopnja značilnosti `α` | `0,05` |

Skupaj smo izvedli **50.000 ponovitev protokola** (25 kombinacij × 2000 ponovitev). V vsaki ponovitvi naključno izberemo 1000 različnih bitov po uskladitvi baz; manjši kontrolni vzorci so začetki istega izbora, zato med seboj niso neodvisni.

Pri 20-% verjetnosti prestrezanja in kontrolnem vzorcu 300 bitov se je izmerjeni TPR ob povečanju osnovnega QBER s 3 % na 25 % zmanjšal s **97,75 % na 24,70 %**.

## Struktura projekta

```text
src/bb84/
  protocol.py                 priprava in prenos kvbitov, Eve, šum, uskladitev baz
  analysis.py                 QBER, kontrolni vzorci, binomski test
  experiments.py              zagon eksperimentov, povzetki in grafi

tests/                        testi protokola, analize in eksperimentov

scripts/
  bootstrap.sh                priprava Python okolja
  build_report.sh             prevajanje seminarske v PDF
  prepare_final_figures.py    izvoz končnih grafov iz shranjenih podatkov

report/
  Skupina22/main.tex          besedilo seminarske naloge
  Skupina22/img/              slike, vključene v poročilo
  evidence/                   povzetek rezultatov in podatki o njihovem izvoru
  references.bib              bibliografija poročila
  editor.tex                  glavna datoteka za prevajanje LaTeXa

pyproject.toml                opis paketa in konfiguracija orodij
requirements.lock             zaklenjene Python odvisnosti
uv.lock                       zaklep odvisnosti za uv
```

Ostale datoteke v mapi `report/` so del predloge LaTeX.

## Namestitev

Potrebujemo **Linux**, **Python 3.11–3.14** in dostop do interneta za namestitev odvisnosti. Iz korenske mape projekta izvedemo:

```bash
bash scripts/bootstrap.sh
source .venv/bin/activate
```

Skripta ustvari navidezno okolje `.venv`, namesti zaklenjene odvisnosti in projekt kot Python paket. Če je okolje že ustvarjeno, uporabi obstoječega. Za izbiro Pythona ob prvi namestitvi lahko nastavimo npr. `BB84_PYTHON=python3.14`.

### Testi

```bash
python -m pytest -q
python -m ruff check .
```

## Zagon eksperimentov

Ukaze izvajamo iz **korenske mape repozitorija** z aktiviranim Python okoljem.

Kratek preizkus vseh kombinacij parametrov:

```bash
python -m bb84.experiments --repetitions 1 --workers 2 --output-dir results/test
```

Celotni eksperiment (50.000 ponovitev):

```bash
python -m bb84.experiments --repetitions 2000 --output-dir results/final
```

Rezultati se shranijo v izbrano mapo. Ponovni zagon z istimi parametri nadaljuje manjkajoče ponovitve; za neodvisen zagon uporabimo drugo mapo. Celotni eksperiment je računsko zahteven.

Za ponovno izdelavo povzetkov in grafov iz že shranjenega CSV, brez novih simulacij:

```bash
python -m bb84.experiments --summarize-only --output-dir results/final
```

Ta ukaz prepiše izpeljane povzetke in grafe v navedeni mapi, ne pa izvornih podatkov o posameznih ponovitvah.

### Rezultati

- `h1_h2_trials.csv` – rezultati posameznih ponovitev in šestih kontrolnih vzorcev.
- `h1_h2_summary.csv` – TPR/FPR, 95-% Wilsonovi intervali zaupanja in teoretične napovedi.
- `h1_tpr_vs_sample.png` – vpliv velikosti kontrolnega vzorca.
- `h2_tpr_vs_noise.png` – vpliv šuma.
- `fpr_vs_sample.png` – lažni alarmi brez prisotnosti Eve.

Za pripravo končnih grafov v formatih PNG, PDF in SVG iz popolnega nabora rezultatov:

```bash
python scripts/prepare_final_figures.py \
  --source results/final/h1_h2_trials.csv \
  --output-dir results/final-figures
```

Izhodna mapa mora biti nova in vhodni CSV mora vsebovati vseh 50.000 ponovitev. Skripta doda tudi povzetek, kopijo podatkov in informacije o izvoru grafov.

## Seminarska naloga

Besedilo se nahaja v `report/Skupina22/main.tex`, uporabljena literatura pa v `report/references.bib`. Za pripravo PDF potrebujemo nameščen **TeX Live** s potrebnimi paketi in orodjem `latexmk`.

```bash
bash scripts/build_report.sh
```

Končni dokument se ustvari v `report/build/editor.pdf`. V repozitoriju so že vključeni tudi PDF-grafi, uporabljeni v poročilu.

## Ponovljivost in omejitve

- Eksperimenti uporabljajo določena naključna semena, kar omogoča ponovitev v primerljivem programskem okolju.
- Popolni podatki posameznih 50.000 ponovitev niso vključeni v Git. V `report/evidence/` sta shranjena povzetek glavnih rezultatov in zapis njihovega izvora. Za ponovitev analize iz surovih podatkov jih je treba pridobiti ločeno ali ponovno izvesti eksperiment.
- Različice okolja prvotnih simulacij niso zapisane v izvornem CSV. Kasnejše preverjanje projekta oziroma priprava grafov zato ne dokazuje, da so bile prvotne simulacije izvedene z istimi različicami knjižnic.
- Model predpostavlja znan osnovni QBER, neodvisne prenose in idealno pripravo ter meritev kvbitov. Obravnava samo depolarizacijski šum in napad *intercept-resend*.
- Zaznava statističnega odstopanja od modela šuma **ni dokaz varnosti končnega skrivnega ključa**. Projekt ne vključuje popravljanja napak in ojačanja zasebnosti.

Podrobnejša metodologija, rezultati in primerjava z literaturo so predstavljeni v seminarski nalogi.
