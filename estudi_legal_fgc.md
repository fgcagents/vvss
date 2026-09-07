# Estudi personalitzat: restriccions i parametres legals
## Servei de vigilancia FGC — Sabico / Trablisa (serveis sense arma de foc)

## 0. Advertiment metodologic — llegiu-ho abans de confiar en els valors

**No existeix un "conveni FGC-Sabico-Trablisa" com a document unic.** He buscat
expressament un conveni d'empresa de Sabico Seguridad i de Trablisa al registre
de convenis del BOE i no n'hi ha cap de publicat: com la gran majoria d'empreses
de seguretat privada a Espanya, totes dues es regeixen pel **Conveni Col·lectiu
Estatal d'Empreses de Seguretat** (sectorial), no per un conveni propi.

El que SI es especific de FGC son dos documents que no formen part del conveni
laboral:

1. **El contracte de servei / plec de condicions** entre FGC i cada empresa
   concessionaria (fixa cobertures, lots per linia, preu/hora, etc.).
2. **El Pla de Seguretat de Ferrocarrils**, avalat pels Mossos d'Esquadra, que
   imposa requisits operatius per damunt del mínim del conveni (per exemple, el
   requisit de treballar en parella que veureu a la secció 2).

**No he pogut accedir al text exacte del plec vigent** perque el portal de
contractacio publica (contractaciopublica.gencat.cat) bloqueja l'accés
automatitzat. Si hi teniu accés intern (com a treballador/a del sector),
val molt la pena baixar-lo — probablement especifica cobertures exactes
per estacio que ara mateix nomes puc aproximar.

## 1. Qui opera que (confirmat vs. assumit)

| Fet | Estat |
|---|---|
| Trablisa es una de les empreses concessionaries del servei de seguretat de FGC, concretament a la Linia del Valles (Barcelona-Valles) | **Confirmat** (premsa, protesta de desembre 2024 a l'estacio de Sant Cugat / Lluis Millet) |
| Sabico Seguridad, S.A. opera/ha operat en contractes de seguretat de FGC i d'altres ens de la Generalitat | **Confirmat que hi participa com a licitadora/adjudicataria** en contractes relacionats (p. ex. videovigilancia del Funicular de Gelida); **NO confirmat** amb font publica quina linia/lot de FGC cobreix ara mateix |
| El contracte marc actual de vigilancia de FGC (~21,4M€, 2 anys) cobreix Barcelona-Valles, Llobregat-Anoia i Lleida-La Pobla de Segur, dividit en lots | **Confirmat** (nota de premsa del Govern, abril 2026) — la divisio en lots explica per que hi ha mes d'una empresa concessionaria operant alhora |
| FGC exigeix contractualment a les concessionaries complir el conveni de seguretat privada i l'Estatut dels Treballadors | **Confirmat**, declaracions de FGC arran del conflicte amb Trablisa |

**Recomanacio**: confirmeu internament si Sabico cobreix Llobregat-Anoia o
Lleida-La Pobla de Segur — aixo determina si heu de modelar una sola zona
operativa o diverses amb parametres potencialment diferents per lot/contracte.

## 2. Taula de parametres: font legal -> parametre al codi

| Requisit | Font | Valor trobat | On viu al codi |
|---|---|---|---|
| Descans minim entre jornades | Conveni sectorial 2026-2030 | 13h general / 12h auxiliars de servei | `ParametresLegals.descans_minim_hores` / `.descans_minim_auxiliars_hores` |
| Descans setmanal obligatori | Conveni + Estatut dels Treballadors | >=1 dia lliure de cada 7, en **finestra mobil** (no partició fixa dilluns-diumenge) | Seccio 4 de `model.py` — reescrita expressament arran del cas de Trablisa (vegeu 3) |
| Jornada maxima setmanal | Conveni sectorial | 40h ordinaries / fins a 48h amb hores extres | `Vigilant.hores_max_setmana` |
| Jornada anual de referencia (temps complet) | Conveni 2026-2030 | 1.782h efectives/any | `Vigilant.hores_objectiu_periode` (prorrategeu-lo al periode que planifiqueu) |
| Categories sense arma de foc | Confirmat pel context (serveis FGC sense arma) | Nomes `"no_armat"` i `"cctv"` — s'ha eliminat la categoria `"armat"` del prototip | `Vigilant.habilitacions` / `Servei.habilitacio_requerida` a `dades_exemple.py` |
| Reforc nocturn / treball en parella | **Pla de Seguretat de FGC**, avalat pels Mossos d'Esquadra | Vigilants **en parella de 22h a 6h** i en "situacions singulars"; en unitat (1 sol) la resta de l'horari i situacions | `Servei.vigilants_requerits = 2` per als serveis que solapen 22:00-06:00 (`requerits_per_torn()` a `dades_exemple.py`) |
| Servei continu | Contracte FGC | 24 hores, 365 dies/any | Horitzo de planificacio sense buits |
| Plusos nocturnitat/festius | Conveni sectorial | Varien per categoria; s'actualitzen anualment 2026-2030 | **No inclos encara** a la funcio de cost — nomes rellevant si voleu optimitzar cost, no nomes hores |
| Franc obligatori nit de 24/31 desembre | Conveni 2026-2030 | Nit lliure obligatoria, amb extensio de descans | **No inclos encara** — cal afegir-ho com a restriccio puntual per calendari |
| Descans compensatori en serveis molt llargs (24h) | Practica habitual del sector (no un article unic del conveni sectorial) | Configurable — per defecte al prototip: si un torn dura >=20h, descans posterior de 48h | `ParametresLegals.llindar_torn_llarg_hores` / `.descans_torn_llarg_hores` — **com que els serveis de FGC que conec son per torns de 8h, aquest paràmetre probablement no us apliqui; deixeu-lo pero no el doneu per bo sense confirmar-ho** |

## 3. Perque la finestra de descans es ara "mobil" i no per setmanes fixes

La protesta de Trablisa (desembre 2024, Linia del Valles) denuncia
explícitament **torns de 12 dies seguits sense descans**, a mes de
desproteccio en agressions i us de les camares per "control laboral". Aixo
es un incompliment real i documentat del descans setmanal **al mateix
servei que esteu modelant**.

Amb una restriccio de descans basada en particions fixes de calendari
(dilluns-diumenge), es facilment possible que el motor consideri "correcte"
un pla amb el dia de descans el diumenge d'una setmana i el dilluns
següent — es a dir, fins a 12-13 dies seguits treballats sense violar
tecnicament la restriccio, exactament el patró denunciat. Per aixo la
versio actual de `model.py` comprova **cada finestra de 7 dies consecutius**
(no nomes els blocs de calendari), garantint que mai hi hagi mes de 6 dies
seguits treballats, caigui on caigui el dia de descans.

## 4. El requisit de "parella nocturna" com a restriccio de cobertura, no com a regla nova

No calia afegir cap mecanisme nou al motor per al requisit de treballar en
parella: ja teniu `Servei.vigilants_requerits`, pensat originalment per
cobertures generiques. El que calia era **posar-hi el valor correcte**:
`2` per a qualsevol servei que solapi la franja 22:00-06:00 (i, si en
teniu la definicio exacta, per a les "situacions singulars" que esmenta
FGC — ara mateix no en tinc una llista tancada i verificable, caldria
confirmar-la amb el Pla de Seguretat complet).

## 5. Que falta per tancar l'estudi (no ho puc verificar per cerca web)

- Text vigent del plec de prescripcions tecniques (cobertures exactes per
  estacio i franja, i quin lot cobreix Sabico).
- Confirmacio de si Sabico o Trablisa tenen algun pacte d'empresa intern
  que ampliï els minims del conveni sectorial (no n'he trobat cap de
  public — probablement no en tenen, com la majoria del sector).
- Definicio tancada de les "situacions singulars" que, segons FGC, tambe
  exigeixen parella (ara nomes cobreixo la franja horaria 22-06h).
- Import exacte dels plusos de nocturnitat/festius si voleu que la funcio
  de cost optimitzi tambe cost economic i no nomes equilibri d'hores.
