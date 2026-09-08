# CP-SAT per a quadrants de vigilants de seguretat en transport ferroviari

Prototip que aplica el mateix enfocament del motor CP-SAT de **Xivato**
(prioritat per hores acumulades + preferencia de zona/torn) a un sector amb
restriccions legals mes dures: la vigilancia de seguretat privada en una
xarxa ferroviaria de passatgers.

## 1. Que es diferent respecte del motor actual de Xivato

El disseny "organic" que ja teniu (connectar per preferencia, filtrar per
capes) funciona be quan la restriccio principal es la preferencia i
l'equilibri d'hores. En seguretat privada hi ha, a mes, **restriccions
dures no negociables** que cal aplicar *abans* de qualsevol capa de
preferencia:

- **Habilitacio/TIP i categoria**: un vigilant nomes pot cobrir un servei
  si te la categoria requerida (per a FGC, serveis sense arma de foc:
  no armat / operador CCTV). No es una preferencia, es un requisit legal
  — si no es compleix, el servei simplement no es pot cobrir amb aquella
  persona.

> **Cas concret FGC (Sabico/Trablisa)**: vegeu `estudi_legal_fgc.md` per
> a l'estudi personalitzat amb els parametres reals trobats (descansos,
> el requisit de treballar en parella de 22h a 6h segons el Pla de
> Seguretat de FGC, i que no hi ha un "conveni FGC" separat — s'aplica
> el conveni sectorial).
- **Descans minim entre jornades**: el conveni estatal de seguretat
  privada fixa un descans general de 13h entre jornada i jornada (12h
  per a auxiliars de serveis), amb regims especials per a torns llargs.
- **Jornada anual de referencia**: el conveni 2026-2030 fixa 1.782 hores
  de treball efectiu/any com a jornada tipus a temps complet — util com a
  objectiu proporcional si voleu portar el mateix criteri de "qui te
  menys hores, te prioritat" que ja useu a Xivato, pero amb la xifra
  correcta del sector (en lloc de les ~1.200h que teniu documentades,
  que probablement corresponen a una altra tipologia de contracte o
  col·lectiu).
- **Cobertura minima simultania per lloc**: als serveis ferroviaris el
  nombre de vigilants necessaris per torn depen del contracte amb
  l'operador (ADIF/Renfe/FGC o similar) i sol variar per estacio i franja
  horaria (hora punta vs. nocturna), no nomes per "servei obert/tancat".

Font principal consultada: Convenio Colectivo Estatal de Empresas de
Seguridad 2026-2030 (BOE) i anàlisis derivades. **Recomanació**: abans de
donar per bons els parametres (`ParametresLegals` a `model.py`), contrasteu-los
amb el pacte d'empresa concret i el plec de condicions del client
ferroviari, perque el conveni marca minims pero cada empresa/contracte hi
pot afegir condicions mes estrictes (per exemple, els descansos
compensatoris despres d'un servei de 24h solen fixar-se per pacte
d'empresa, no pel conveni sectorial).

## 2. Com esta modelat (`model.py`)

- **Variables**: `x[vigilant, servei] = 1` si aquell vigilant cobreix
  aquell servei. Nomes es crea la variable si el vigilant te
  l'habilitacio requerida — aixi la restriccio d'habilitacio queda
  garantida per construccio, no cal afegir-la com a restriccio a part.
- **Restriccions dures**:
  1. Cobertura per servei (amb variable de "deficit" opcional, per si la
     plantilla no dona abast — millor detectar-ho que forçar
     infactibilitat).
  2. Incompatibilitat entre parells de serveis que se solapen o no
     respecten el descans minim (calculat servei a servei, tenint en
     compte el regim especial per a torns >= 20h).
  3. Jornada maxima setmanal per vigilant.
  4. Com a minim un dia lliure per setmana.
- **Funcio objectiu** (dues capes, com al vostre motor "per prioritats"):
  1. Minimitzar la desviacio de cada vigilant respecte del seu objectiu
     d'hores del periode (pes alt).
  2. Maximitzar zona/torn preferits (pes baix, nomes desempata).
  3. Penalitzacio molt alta per cada servei no cobert, per fer visible on
     falta plantilla en lloc d'amagar-ho.

## 3. Prova amb dades sintetiques

`dades_exemple.py` simula 3 punts (Central/Nord/Sud), 7 dies, torns
mati/tarda/nit + un servei armat, amb una plantilla de 8 persones
(deliberadament curta per veure com el solver prioritza i on queden
buits). Executeu:

```bash
pip install ortools
python3 main.py
```

Genera `quadrant.csv` (mateix esperit que els CSV de la simulacio de
gener que ja feieu) i mostra per consola l'estat del solver, els buits de
cobertura i les hores finals per vigilant.

## 4. Com connectar-ho amb Xivato

- El pipeline `DADES VIGENTS -> GENERAR PROPOSTA -> REVISAR -> VALIDAR ->
  PUBLICAR BLOC` es manté igual; aquest motor només canvia com es genera
  la PROPOSTA quan el domini és vigilancia (afegint les restriccions
  dures abans esmentades).
  Substituir `dades_exemple.py` per una lectura real de:
  - plantilla amb habilitacions/TIP vigents (i data de caducitat, per
    poder avisar abans que caduqui),
  - el pla de serveis contractats (per estacio/tram, amb la cobertura
    exigida contractualment),
  - hores acumulades reals de cada vigilant fins la data.
- El resultat parcial (`cobertura_incompleta`) és una senyal directa de
  sots-dimensionament de plantilla — útil per a planificació, no només
  per a l'operativa diària.

## 4bis. Horitzo mobil: congelar el publicat, donar pistes de la resta

Inspirat en l'article sobre L-RHO (MIT) que vau compartir -- la seva idea és
entrenar un model de ML que, en fer avançar l'horitzó de planificació,
decideix quines variables de la solució anterior val la pena "congelar" en
lloc de tornar-les a calcular. Nosaltres NO tenim (encara) un model de ML,
però el mateix principi es pot aplicar de forma senzilla i sense ML, i
encaixa exactament amb el vostre flux real (finestra de 5 dies, es publica
dia a dia):

- `resol()` accepta ara `assignacions_fixades` (dies ja **publicats** --
  restricció dura, el solver no els toca) i `pistes_calents` (dies encara
  **temptatius** de l'última resolució -- es passen via `model.AddHint()`,
  no obliguen res, només guien la cerca).
- **Correcció important que això ha destapat**: si cada finestra de 5 dies
  es resol sense veure res d'abans, les restriccions de descans (el buit
  mínim entre torns i la finestra mòbil de 7 dies) no poden detectar un
  incompliment que travessi la frontera de la finestra (p.ex. un torn de
  nit ahir, just abans d'on comença la finestra d'avui). `rolling_horizon_demo.py`
  ho soluciona afegint 2 dies de "look-back" ja publicats a cada finestra,
  fixats com a `assignacions_fixades`.
- **Resultat honest de la prova** (`rolling_horizon_demo.py`, 8 vigilants,
  finestra de 5 dies sobre un horitzó de 12): a aquesta escala tan petita
  NO hi ha diferència de temps mesurable entre resoldre amb pistes o sense
  -- CP-SAT resol un problema d'aquesta mida en <0,1s de totes maneres. El
  benefici real de les pistes (i, més endavant, d'un model de ML que
  decideixi què congelar) només es notarà quan escaleu a la xarxa sencera
  de FGC (moltes més estacions/línies i vigilants), que és exactament
  l'escala on l'article original diu que els resolvedors tradicionals
  comencen a anar lents.
- **Relacio amb el que ja vau trobar al gener** (V31/V32 vs V34/V35/V36):
  el problema de correlacio d'hores entre lots i l'augment de canvis de
  zona/torn com a compromís és, essencialment, un efecte de frontera
  d'horitzó -- exactament el que aquesta tecnica ataca. Val la pena provar
  `pistes_calents` sobre les vostres dades reals per veure si redueix
  aquest "churn" sense perdre la millora d'equilibri d'hores.
- **Cap a un L-RHO complet (mes endavant, no ara)**: si en el futur teniu
  prou historial de resolucions successives (les simulacions V31-V36 ja en
  son un embrió), es podria entrenar un classificador senzill (per
  exemple, gradient boosting) que predigui per a cada `(vigilant, servei)`
  temptatiu si val la pena fixar-lo abans de resoldre, en lloc de nomes
  donar-lo com a pista. Pero amb el volum de dades actual, la heuristica
  "congela el publicat, pista la resta" ja recull la major part del
  benefici practic sense necessitat de pipeline de ML.

## 5. Limitacions conegudes / properes passes

- Els valors de `ParametresLegals` són el mínim legal general que hem
  trobat al conveni sectorial — **no substitueixen una revisió amb el
  vostre departament legal/laboral**, sobretot per als descansos
  compensatoris de serveis de 24h, que solen dependre del pacte
  d'empresa.
- No modela encara: vacances/baixes com a interval (ara només
  `actiu=False` tot el període), el franc obligatori de 24/31 de
  desembre, ni els plusos de nocturnitat/festius en la funció de cost
  (rellevant si en algun moment voleu optimitzar cost i no només
  equilibri d'hores).
- El graf d'incompatibilitats entre serveis (pas 2) és O(n²) per
  vigilant; per a un mes sencer amb centenars de serveis caldrà indexar
  per finestra temporal en lloc de comparar tots els parells.
