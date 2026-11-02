# Vpliv šuma in velikosti kontrolnega vzorca na zaznavanje prisluškovanja v protokolu BB84

**Seminarska naloga — Nekonvencionalne platforme in metode procesiranja (NPMP)**  
Univerza v Ljubljani, Fakulteta za računalništvo in informatiko — magistrski študij

> **Status:** Odobrena tema. Projekt je v fazi priprave razvoja; eksperimentalni rezultati še niso zbrani.

## Namen

Protokol BB84 omogoča kvantno distribucijo ključev (QKD) z uporabo dveh merilnih baz in štirih kvantnih stanj. Prisluškovanje lahko poruši prenesena stanja, vendar napake povzroča tudi šum kanala. Pri omejenem številu preverjenih bitov zato povečana stopnja napak ne pomeni nujno prisotnosti prisluškovalca.

**Cilj seminarske naloge** je s simulacijami v Pythonu in Qiskitu raziskati, kako **stopnja kvantnega šuma** in **velikost kontrolnega vzorca** vplivata na zmožnost zaznave napada *intercept-resend*. Simulacije bomo primerjali z analitičnimi napovedmi in ocenili kompromis med zaznavanjem napadov ter lažnimi alarmi.

## Raziskovalno vprašanje

**Kako stopnja kvantnega šuma in velikost kontrolnega vzorca vplivata na verjetnost pravilnega zaznavanja prisluškovanja v protokolu BB84?**

Preverili bomo tri hipoteze:

- **H1:** Pri enaki stopnji šuma večji kontrolni vzorec praviloma izboljša verjetnost zaznave napada, če je kriterij odločanja ustrezno umerjen.
- **H2:** Večji šum oteži razlikovanje med legitimnim prenosom in prisluškovanjem, saj povzroča napake tudi brez napadalca.
- **H3:** Za določeno dovoljeno stopnjo lažnih alarmov je mogoče oceniti minimalno velikost kontrolnega vzorca, potrebno za želeno verjetnost zaznave v izbranem modelu napada.

## Model sistema

1. **Alice** naključno izbere bit in bazo \(Z\) ali \(X\), nato pripravi ustrezno stanje \(|0\rangle\), \(|1\rangle\), \(|+\rangle\) ali \(|-\rangle\).
2. **Eve** je lahko odsotna ali prestreže del signalov. Pri napadu *intercept-resend* meri v naključno izbrani bazi in pošlje na novo pripravljeno stanje.
3. Na poti **Eve → Bob** uporabimo enokubitni depolarizacijski kanal. Enako mesto šuma je uporabljeno tudi v scenariju brez Eve.
4. **Bob** neodvisno izbere merilno bazo in izmeri signal.
5. Alice in Bob javno primerjata **bazi**, zadržita le položaje z ujemajočima se bazama (*sifted bits*) in iz njih naključno izbereta **\(m\) kontrolnih bitov**. Njihove vrednosti javno primerjata; kontrolni biti se ne uporabljajo v nadaljnjem ključu.
6. Na kontrolnem vzorcu ocenimo **QBER** in s predhodno določenim statističnim pravilom odločimo, ali je bil napad zaznan.

**Omejitev:** Model ne vključuje vseh korakov praktično varnega QKD, kot so avtentikacija klasičnega kanala, popravljanje napak in ojačanje zasebnosti. Napad *intercept-resend* ni splošen model vseh možnih napadov.

## Glavni parametri in metrike

| Vrsta | Oznaka | Opis |
|---|---|---|
| Neodvisna spremenljivka | \(\lambda\) | Parameter depolarizacijskega kanala (ni enak QBER) |
| Neodvisna spremenljivka | \(m\) | Število javno preverjenih bitov **po uskladitvi baz** |
| Eksperimentalni pogoj | \(p\) | Verjetnost prestrezanja posameznega signala (primarno \(p=0\) in \(p=1\)) |
| Kontrolni parameter | \(N\) | Število prvotno oddanih signalov; mora zagotoviti zadosten *sifted* vzorec |
| Metrika | QBER | Delež napačnih bitov v kontrolnem vzorcu |
| Metrika | TPR / moč testa | Delež poskusov z Eve, v katerih je napad zaznan |
| Metrika | FPR | Delež poskusov brez Eve z lažnim alarmom |
| Metrika | FNR | Delež poskusov z Eve, ko napad ni zaznan |

## Teoretična izhodišča

Za standardni idealni BB84 z naključno izbiro baz in napadom *intercept-resend* brez šuma je pričakovana stopnja napak v usklajenem ključu:

\[
q_{\mathrm{Eve}}=\frac{p}{4}.
\]

Za enokubitni depolarizacijski kanal, ki je v Qiskit Aer definiran kot

\[
\mathcal{D}_{\lambda}(\rho)=(1-\lambda)\rho+\lambda I/2,
\]

je za pravilno izbrano merilno bazo osnovna stopnja napak **brez Eve** \(q_0=\lambda/2\). Če je šum neodvisno uporabljen **za** napadom *intercept-resend*, je za ta poenostavljeni model pričakovana stopnja napak

\[
q_1=\frac{\lambda}{2}+(1-\lambda)\frac{p}{4}.
\]

Parametra \(\lambda\) in \(p\) sta modelna parametra; to nista neposredni verjetnosti zaznave napada.

V idealnem kanalu brez šuma in z odločitvijo »zaznava ob vsaj eni napaki« je pri \(m\) neodvisnih preverjenih bitih:

\[
P(\text{vsaj ena napaka})=1-\left(1-\frac p4\right)^m.
\]

Ta izraz **ni splošen kriterij zaznave v šumnem kanalu**: tam bi tak kriterij povzročal lažne alarme. Za šumne primere bomo uporabili vnaprej določen prag oziroma **enostranski eksaktni binomski test** za \(H_0:q=q_0\) proti \(H_1:q>q_0\) (npr. \(\alpha=0{,}05\)). Rezultati so pogojeni s predpostavko, da je osnovni šum \(q_0\) znan/kalibriran; če ni, je problem zahtevnejši.

## Načrt eksperimentov

### E1 — Preverjanje simulatorja in napada

Pri \(\lambda=0\) primerjamo scenarija brez Eve (pričakovani QBER \(0\)) in s polnim napadom *intercept-resend* (pričakovani QBER približno \(25\,\%\)). Po želji dodamo delno prestrezanje za preverjanje zveze \(p/4\). Gre za validacijo pred glavnima eksperimentoma.

### E2 — Vpliv šuma in velikosti kontrolnega vzorca

Za mrežo vrednosti \(\lambda\) in \(m\) izvedemo ponovljene neodvisne simulacije z Eve in brez nje. Za vsak poskus zabeležimo število kontrolnih napak, QBER in odločitev testa. Primerjamo TPR, FPR in FNR ter označimo intervale zaupanja. Predlagane začetne vrednosti (po pilotnem preizkusu jih lahko prilagodimo):

- \(\lambda\in\{0,0{,}02,0{,}05,0{,}10,0{,}20\}\),
- \(m\in\{16,32,64,128,256,512\}\),
- \(p\in\{0,1\}\), dodatno \(p=0{,}5\) le po potrebi,
- vsaj 200 ponovitev na konfiguracijo kot pilotna nastavitev; končno število določimo glede na natančnost ocene in čas izvajanja.

Pozor: če število signalov \(N\) ne zadostuje za izbrani \(m\), se poskus ne sme tiho izpustiti ali nadomestiti z manjšim kontrolnim vzorcem; protokol mora določiti način ponovitve/prilagoditve \(N\).

### E3 — Primerjava z analitičnimi pričakovanji

Ocenjene stopnje napak in stopnje zaznave primerjamo s teorijo: \(q_0\), \(q_1\) ter binomsko porazdelitvijo \(K\sim\mathrm{Bin}(m,q)\) pri predpostavki neodvisnih signalov. Raziskali bomo, kako velik \(m\) potrebujemo za izbrano zahtevano moč testa pri omejeni stopnji lažnih alarmov.

Predvideni grafi: QBER proti šumu, TPR proti velikosti vzorca pri različnih stopnjah šuma, FPR proti velikosti vzorca ter primerjava teorija–simulacija. Vsi grafi bodo jasno označeni kot dejanske simulacije, analitične krivulje ali primeri.

## Razvojno okolje

- Linux, Python (projektni `.venv`), Qiskit in Qiskit Aer
- NumPy, SciPy (binomski testi), Pandas, Matplotlib
- Pytest in Ruff za preverjanje
- `direnv` za samodejno aktivacijo okolja ob vstopu v mapo

### Prvi zagon in namestitev na drugem računalniku

Po kloniranju samostojnega repozitorija vstopimo v njegovo korensko mapo. Ne potrebujemo dostopa do nadrejenega univerzitetnega repozitorija ali osebnih dotfiles. Potrebujemo Linux, Python z moduloma `venv` in `pip` ter `direnv`. Skripta prednostno poišče Python 3.12, nato 3.11 ali 3.13. Na tem računalniku je na voljo Python 3.13.3; namestitev uporablja pripravljene binarne pakete. Interpreter lahko ob prvi namestitvi določimo z `BB84_PYTHON=python3.12 ./scripts/bootstrap.sh`.

```bash
./scripts/bootstrap.sh
cat .envrc              # pred dovoljenjem pregledamo vsebino
direnv allow .          # enkrat za ta klon oziroma po spremembi .envrc
cd .                    # sproži ponovno nalaganje v Zsh
which python
python -c 'import sys; print(sys.executable); print(sys.prefix)'
python -c 'import bb84, qiskit, qiskit_aer, numpy, scipy, pandas, matplotlib; print(qiskit.__version__, qiskit_aer.__version__)'
```

`bootstrap.sh` ustvari standardno `.venv`, iz `requirements.lock` namesti odvisnosti z zaklenjenimi različicami in preverjanjem SHA-256 ter nato v urejevalnem načinu namesti projekt iz `src/`. Ponovni zagon ohrani obstoječa `.venv` in `.env`; preveri uvoze in skladnost paketov. Skripta ne potrebuje `uv`. Ta je potreben samo pri namerni posodobitvi lockfile; natančen ukaz za ponovno generiranje je v njegovi glavi. Zaklenjene so tudi razvojne in gradilne odvisnosti. Odvisnosti se ob vstopu v mapo ne nameščajo.

`direnv` potrebuje Zsh kavelj `eval "$(direnv hook zsh)"` v dejansko uporabljeni `.zshrc` (upoštevamo `ZDOTDIR` in morebitne simbolne povezave). Na tem računalniku je že nastavljen v `$ZDOTDIR/.zshrc`, kjer je `ZDOTDIR=$HOME/.config/zsh`; obstoječih dotfiles ni treba spreminjati. Na drugem računalniku kavelj dodamo samo, če ga še ni. Navodila: [uradna nastavitev direnv](https://direnv.net/docs/hook.html).

Po enkratnem `direnv allow .` vstop v mapo doda `.venv/bin` na začetek `PATH` in nastavi `VIRTUAL_ENV`; odhod obnovi prejšnje okolje. `.envrc` po potrebi naloži `.env`. Dodatnega samodejnega dotenv nalagalnika za ta projekt ne potrebujemo. Preverjanje: po vstopu mora `which python` kazati projektni `.venv/bin/python`; po `cd /tmp` se obnovi prejšnji `PATH`; ob vrnitvi je projektni Python spet aktiven. Brez `direnv` lahko za posamezen ukaz uporabimo `.venv/bin/python`.

Projektni `.env` je lokalna, v Git prezrta datoteka. `.envrc` je različica, ki jo Git sledi, in ne sme vsebovati skrivnosti. Na drugem računalniku se ustvari ločeno `.venv`, zato projekt ne sme vsebovati absolutnih osebnih poti.

Če `.env` še ne obstaja, ga bootstrap kopira iz `.env.example` z vrednostmi `BB84_SEED=42`, `BB84_SHOTS=1024` in `BB84_OUTPUT_DIR=results`. Te spremenljivke so pripravljene za prihodnjo lastno implementacijo; trenutno jih paket ne uporablja.

### Orodja in lastna implementacija

Paket `src/bb84/__init__.py` je prazen. Protokol, kvantna vezja, izračuni QBER, testi in eksperimenti še niso implementirani. Ukaz `python -m bb84` zato še ni na voljo.

```bash
python -m pip check
python -m ruff --version
python -m pytest --version
python -m ruff check .
# Ko napišemo lastne teste:
python -m pytest
```

Dokler lastnih testov ni, Pytest sporoči `no tests ran` in vrne izhodno kodo 5; to ni uspešno opravljen funkcijski test. Ruff in Pytest sta nastavljena v `pyproject.toml`. Za delo v paru uporabljamo ločene veje in pregled sprememb prek pull requestov; vsak sodelavec ima svoje lokalno okolje.

## Predvidena struktura repozitorija

```text
seminar-1-bb84/
├── README.md
├── pyproject.toml
├── .envrc
├── .env.example
├── src/bb84/                 # osnovni protokol in modeli
├── experiments/              # ponovljivi eksperimenti
├── tests/                    # preverjanje pravilnosti
├── scripts/                  # bootstrap in prenos literature
├── literature/
│   ├── README.md
│   ├── sources.json
│   ├── references.bib
│   └── pdfs/                 # lokalno; brez commita
├── results/                  # CSV rezultatov
├── figures/                  # grafi
└── report/                   # poročilo v slovenščini (LaTeX)
```

Struktura je ciljna; mape nastajajo postopno, ko jih potrebujemo.

## Literatura

Vsa spodnja znanstvena dela so brezplačno dostopna: večina na arXiv, študija Fiorini idr. (2024) pa v odprtodostopni reviji *Future Internet*. Podatki za lokalni prenos bodo v `literature/sources.json`, bibliografija pa v `literature/references.bib`.

| Vir | Namen | Brezplačni PDF |
|---|---|---|
| Bennett in Brassard (1984), *Quantum cryptography: Public key distribution and coin tossing* | Osnove protokola BB84 | [arXiv](https://arxiv.org/pdf/2003.06557) |
| Gisin idr. (2002), *Quantum cryptography* | Merilne baze, prisluškovanje, QBER | [arXiv](https://arxiv.org/pdf/quant-ph/0101098) |
| Scarani idr. (2009), *The security of practical quantum key distribution* | Šum in omejitve praktičnih sistemov QKD | [arXiv](https://arxiv.org/pdf/0802.4155) |
| Cai in Scarani (2009), *Finite-key analysis for practical implementations of quantum key distribution* | Omejeno število bitov in statistično sklepanje | [arXiv](https://arxiv.org/pdf/0811.2628) |
| Tomamichel idr. (2012), *Tight finite-key analysis for quantum cryptography* | Pomen končnih vzorcev in varnostnih meja | [arXiv](https://arxiv.org/pdf/1103.4130) |
| Fiorini idr. (2024), *Estimating interception density in the BB84 protocol: A study with a noisy quantum simulator* | **Neposredna primerjava**: prestrezanje, šum, dolžina vzorca in zaznavanje | [MDPI](https://www.mdpi.com/1999-5903/16/8/275/pdf) |
| Shor in Preskill (2000), *Simple proof of security of the BB84 quantum key distribution protocol* | Dodatno ozadje varnostnih dokazov, ne osrednja literatura eksperimenta | [arXiv](https://arxiv.org/pdf/quant-ph/0003004) |

**Dokumentacija orodij:** [IBM Quantum – QKD](https://qiskit.qotlabs.org/learning/modules/computer-science/quantum-key-distribution), [Qiskit Aer – depolarizing_error](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.depolarizing_error.html), [SciPy – binomtest](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html) in [direnv](https://direnv.net/docs/hook.html).

Po postavitvi lahko literaturo prenesemo z:

```bash
python scripts/fetch_literature.py
```

V `literature/pdfs/` shranjujemo lokalne kopije; **PDF-jev privzeto ne dodajamo v Git**. Za prijavo in zagovor uporabljamo preverjene bibliografske podatke in primarne vire.

## Predvideno poročilo

Poročilo v slovenščini (približno 10 strani, skladno z navodili predmeta): uvod in raziskovalno vprašanje, teoretično ozadje, eksperimentalna metodologija, rezultati, razprava, omejitve in sklep. Prikazali bomo parametre simulatorja, ponovitve, intervale zaupanja, izbrane grafe ter primerjave s teoretičnimi pričakovanji.

## Potek dela

- [ ] Postaviti Python/Qiskit/Aer/direnv okolje in pripraviti prenose literature.
- [ ] Implementirati osnovni idealni BB84 in teste.
- [ ] Implementirati napad *intercept-resend* ter preveriti pričakovanih 25 % QBER.
- [ ] Dodati natančno opredeljen enokubitni depolarizacijski kanal.
- [ ] Implementirati kontrolni vzorec, statistični test in metrike TPR/FPR/FNR.
- [ ] Izvesti ponavljajoče eksperimente ter shraniti podatke in grafe.
- [ ] Primerjati meritve z analitičnim modelom in napisati slovensko poročilo.

## Meje interpretacije

To je raziskava **zaznavanja določenega napada v določenem simulacijskem modelu**. Statistična odločitev o napadu ni varnostni dokaz BB84, QBER sam zase ne razkrije povzročitelja napak, izhod simulacije pa ni neposredno uporaben kot kriptografsko varen končni ključ.
