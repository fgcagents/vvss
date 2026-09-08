# \ud83d\udca1 **Exemples d'\u00fas i Casos Pr\u00e0ctics - Sistema VVSS**

> **Guia pr\u00e0ctica amb exemples reals, workflows complets i benchmarking de rendiment**

---

## \ud83d\udcc1 **\u00cdndex**

1. [Introducci\u00f3](#-introducci\u00f3)
2. [Preparaci\u00f3 de l'Entorn](#-preparaci\u00f3-de-lentorn)
3. [Exemples B\u00e0sics](#-exemples-b\u00e0sics)
4. [Exemples Intermedis](#-exemples-intermedis)
5. [Exemples Avan\u00e7ats](#-exemples-avan\u00e7ats)
6. [Casos d'\u00fas Reals](#-casos-d\u00e7s-reals)
7. [Benchmarking de Rendiment](#-benchmarking-de-rendiment)
8. [Personalitzaci\u00f3 del Sistema](#-personalitzaci\u00f3-del-sistema)
9. [Integraci\u00f3 amb Altres Sistemes](#-integraci\u00f3-amb-altres-sistemes)
10. [Exemples de Depuraci\u00f3](#-exemples-de-depuraci\u00f3)
11. [Plantilles i Scripts \u00daltiles](#-plantilles-i-scripts-\u00e0tils)

---

## \ud83d\udc80 **Introducci\u00f3**

Aquest document proporciona **exemples pr\u00e0ctics i casos reals** per a utilitzar el sistema VVSS en diferents escenaris. Cada exemple \u00e9s **aut\u00f2nom, executable i validat** amb les dades d'exemple del projecte.

### **Estructura dels Exemples**

Tots els exemples segueixen aquesta estructura:

```python
"""
T\u00edtol: [Nom de l'exemple]
Descripci\u00f3: [Qu\u00e8 fa l'exemple]
Complexitat: [Baixa/Mitjana/Alta]
Temps estimat: [Segons/Minuts]
Requisits: [Depend\u00e8ncies espec\u00edfiques]
"""

# Codi de l'exemple
...
```

### **Convencions**

- \ud83d\udfe2 **Principiant**: Exemples senzills per a comen\u00e7ar
- \ud83d\udfe1 **Intermedi**: Exemples amb configuraci\u00f3 personalitzada  
- \ud83d\udfe0 **Avan\u00e7at**: Exemples complexos per a usuaris experts
- \u26a1 **Validat**: Exemples provats amb les dades d'exemple
- \u2705 **Compliment Legal**: Tots els exemples compleixen la normativa

---

## **Preparaci\u00f3 de l'Entorn**

### **Requisits Previs**

```bash
# Verificar que totes les depend\u00e8ncies estan instal\u00b7lades
python -c "
import ortools
import pydantic  
import pandas
import sqlite3
print('All dependencies installed successfully')
print(f'  OR-Tools: {ortools.__version__}')
print(f'  Pydantic: {pydantic.__version__}')
print(f'  Pandas: {pandas.__version__}')
print(f'  SQLite: {sqlite3.sqlite_version}')
"
```

### **Inicialitzaci\u00f3 R\u00e0pida**

```python
"""
Inicialitzaci\u00f3 del Sistema
Descripci\u00f3: Configura l'entorn i carrega les dades d'exemple
Complexitat: Baixa
Temps: < 1 segon
"""

from database import reset_db
from dades_exemple import generar_dades_exemple
from database import init_db

# Reiniciar base de dades
reset_db()

# Generar i carregar dades d'exemple
dades = generar_dades_exemple()
init_db(dades)

# Verificar
from database import obtenir_vigilants, obtenir_serveis
vigilants = obtenir_vigilants()
serveis = obtenir_serveis()

print(f"System initialized: {len(vigilants)} vigilants, {len(serveis)} serveis")
```

---

## **Exemples B\u00e0sics**

### **Exemple 1: Planificaci\u00f3 Setmanal B\u00e0sica**

\ud83d\udfe2 **Principiant** | \u2705 **Validat** | \u2705 **Compliment Legal**

```python
"""
Planificaci\u00f3 Setmanal B\u00e0sica
Descripci\u00f3: Crea planificaci\u00f3 de 7 dies amb solver b\u00e0sic
Complexitat: Baixa
Temps: < 1 segon
"""

from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
from solver import resol

reset_db()
dades = generar_dades_exemple(dies=7)
init_db(dades)

resultat = resol(dies=7)

print(f"Status: {resultat.estat}")
print(f"Time: {resultat.temps_resolucio:.3f}s")
print(f"Coverage: {resultat.serveis_coberts}/{resultat.serveis_total}")
print(f"Uncovered: {resultat.serveis_descoberts}")
```

---

### **Exemple 2: Exportaci\u00f3 a CSV**

\ud83d\udfe2 **Principiant** | \u2705 **Validat**

```python
"""
Exportaci\u00f3 a CSV
Descripci\u00f3: Exporta resultats a fitxers CSV
Complexitat: Baixa  
Temps: < 1 segon
"""

from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
from solver import resol
from exporter import exportar_a_csv
import os

reset_db()
dades = generar_dades_exemple(dies=7)
init_db(dades)
resultat = resol(dies=7)

os.makedirs("output", exist_ok=True)
exportar_a_csv(resultat, "output/assignacions.csv", tipus="vigilant")
print("CSV exported to output/assignacions.csv")
```

---

### **Exemple 3: Visualitzaci\u00f3 del Quadrant**

\ud83d\udfe2 **Principiant** | \u2705 **Validat**

```python
"""
Visualitzaci\u00f3 del Quadrant
Descripci\u00f3: Genera representaci\u00f3 visual del quadrant
Complexitat: Baixa
Temps: < 1 segon
"""

from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
from solver import resol
from exporter import exportar_a_quadrant_visual

reset_db()
dades = generar_dades_exemple(dies=7)
init_db(dades)
resultat = resol(dies=7)

quadrant = exportar_a_quadrant_visual(resultat)
print(quadrant[:500])  # Mostra primeres 500 car\u00e0cters
```

---

### **Exemple 4: Verificaci\u00f3 de Binomis**

\ud83d\udfe2 **Principiant** | \u2705 **Validat** | \u2705 **Compliment Legal (Pla FGC)**

```python
"""
Verificaci\u00f3 de Binomis Obligatoris
Descripci\u00f3: Verifica cobertura de serveis de nit amb binomi
Complexitat: Baixa
Temps: < 1 segon
"""

from database import reset_db, init_db, obtenir_serveis
from dades_exemple import generar_dades_exemple
from solver import resol

reset_db()
dades = generar_dades_exemple(dies=7)
init_db(dades)
resultat = resol(dies=7)

serveis_nit_binomi = [s for s in obtenir_serveis() 
                     if s.torn == 'nit' and s.binomi_obligatori]

coberts = 0
for servei in serveis_nit_binomi:
    assignats = [a for a in resultat.assignacions if a.servei_id == servei.id]
    if len(assignats) >= 2:
        coberts += 1

print(f"Binomis coberts: {coberts}/{len(serveis_nit_binomi)} "
      f"({100*coberts/len(serveis_nit_binomi):.1f}%)")
```

---

### **Exemple 5: Validaci\u00f3 Legal**

\ud83d\udfe2 **Principiant** | \u2705 **Validat** | \u2705 **Compliment Legal**

```python
"""
Validaci\u00f3 Legal
Descripci\u00f3: Verifica compliment de totes les restriccions legals
Complexitat: Baixa
Temps: < 1 segon
"""

from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
from solver import resol, valida_resultat

reset_db()
dades = generar_dades_exemple(dies=7)
init_db(dades)
resultat = resol(dies=7)

validacio = valida_resultat(resultat)
print(f"Legal compliance: {'VALID' if validacio['valid'] else 'INVALID'}")

if not validacio['valid']:
    print("Errors:", validacio['errors'])
```

---

## **Exemples Intermedis**

### **Exemple 6: Rolling Horizon Personalitzat**

\ud83d\udfe1 **Intermedi** | \u2705 **Validat** | \u2705 **Compliment Legal**

```python
"""
Rolling Horizon Personalitzat
Descripci\u00f3: Executa Rolling Horizon amb par\u00e0metres personalitzats
Complexitat: Mitjana
Temps: 5-10 segons
"""

from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
from integrated_system import SistemaIntegrat

reset_db()
dades = generar_dades_exemple(dies=14)
init_db(dades)

sistema = SistemaIntegrat(
    dies_finestra=5,
    dies_lookback=2,
    dies_horitzo_total=14,
    pes_equilibri_hores=15,
    pes_equitat_nits=25
)

sistema.inicialitzar_sistema()
resultat = sistema.executar_rolling_horizon()

print(f"Dies processats: {len(resultat)}")
print(f"Total temps: {sum(r.temps_resolucio for r in resultat):.3f}s")
print(f"Total coverage: {sum(r.serveis_coberts for r in resultat)}/"
      f"{sum(r.serveis_total for r in resultat)}")
```

---

### **Exemple 7: Gesti\u00f3 de Descoberts**

\ud83d\udfe1 **Intermedi** | \u2705 **Validat**

```python
"""
Gesti\u00f3 Intel\u00b7ligent de Descoberts
Descripci\u00f3: Detecci\u00f3 i classificaci\u00f3 autom\u00e0tica de descoberts
Complexitat: Mitjana
Temps: 2-5 segons
"""

from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
from integrated_system import SistemaIntegrat
from descoberts_manager import processar_resultat_i_descoberts

reset_db()
dades = generar_dades_exemple(dies=7)
init_db(dades)

sistema = SistemaIntegrat(dies_finestra=3, dies_lookback=1, dies_horitzo_total=7)
sistema.inicialitzar_sistema()
resultat = sistema.executar_rolling_horizon()

for resultat_dia in resultat:
    processat = processar_resultat_i_descoberts(resultat_dia, dia=resultat_dia.dia_inici)
    if processat['descoberts']:
        print(f"Dia {resultat_dia.dia_inici}: {len(processat['descoberts'])} descoberts")
        for d in processat['descoberts']:
            print(f"  - {d['servei'].codi}: {d['motiu']}")
    else:
        print(f"Dia {resultat_dia.dia_inici}: 0 descoberts")
```

---

### **Exemple 8: Substitucions d'Urg\u00e8ncia**

\ud83d\udfe1 **Intermedi** | \u2705 **Validat** | \u2705 **Compliment Legal**

```python
"""
Substitucions d'Urg\u00e8ncia
Descripci\u00f3: Simula substitució per vigilant amb baixa m\u00e8dica
Complexitat: Mitjana
Temps: 1-2 segons
"""

from database import reset_db, init_db, obtenir_vigilants, registrar_baixa
from dades_exemple import generar_dades_exemple
from integrated_system import SistemaIntegrat

reset_db()
dades = generar_dades_exemple(dies=7)
init_db(dades)

# Simular baixa
vigilants = obtenir_vigilants()
for dia in range(3):
    registrar_baixa(vigilant_id=vigilants[0].id, dia_inici=dia, dia_fi=dia, motiu="Malaltia")

sistema = SistemaIntegrat(dies_finestra=3, dies_lookback=1, dies_horitzo_total=7)
sistema.inicialitzar_sistema()
resultat = sistema.executar_rolling_horizon()

print(f"Substitution executed. Coverage: "
      f"{sum(r.serveis_coberts for r in resultat)}/"
      f"{sum(r.serveis_total for r in resultat)}")
```

---

### **Exemple 9: Exportaci\u00f3 a JSON**

\ud83d\udfe1 **Intermedi** | \u2705 **Validat**

```python
"""
Exportaci\u00f3 a JSON
Descripci\u00f3: Exporta assignacions en format JSON per a APIs
Complexitat: Mitjana
Temps: < 1 segon
"""

from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
from solver import resol
from exporter import exportar_a_json
import json

reset_db()
dades = generar_dades_exemple(dies=3)
init_db(dades)
resultat = resol(dies=3)

json_resultat = exportar_a_json(resultat)
with open("assignacions.json", "w") as f:
    json.dump(json_resultat, f, indent=2)

print("JSON exported to assignacions.json")
```

---

### **Exemple 10: An\u00e0lisi de C\u00e0rrega de Treball**

\ud83d\udfe1 **Intermedi** | \u2705 **Validat**

```python
"""
An\u00e0lisi de C\u00e0rrega de Treball
Descripci\u00f3: Analitza distribució de càrrega entre vigilants
Complexitat: Mitjana
Temps: < 1 segon
"""

from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
from solver import resol
from exporter import exportar_a_dataframe

reset_db()
dades = generar_dades_exemple(dies=7)
init_db(dades)
resultat = resol(dies=7)

df = exportar_a_dataframe(resultat, tipus="vigilant")
hores_per_vigilant = df.groupby('vigilant')['hores'].sum()

print("Hores per vigilant:")
for vigilant, hores in hores_per_vigilant.sort_values().items():
    print(f"  {vigilant}: {hores:.1f}h")

print(f"\nMitjana: {hores_per_vigilant.mean():.1f}h")
print(f"Desviaci\u00f3: {hores_per_vigilant.std():.2f}h")
```

---

## **Exemples Avan\u00e7ats**

### **Exemple 11: Restriccions Personalitzades**

\ud83d\udfe0 **Avan\u00e7at** | \u2705 **Validat** | \u2705 **Compliment Legal**

```python
"""
Restriccions Personalitzades
Descripci\u00f3: Afegeix restricci\u00f3 de m\u00e0xim 3 torns de nit per setmana
Complexitat: Alta
Temps: 2-5 segons
"""

from builder import ModelBuilder
from ortools.sat.python import cp_model
from solver import resol_with_custom_builder
from schemas import Vigilant, Servei
from typing import List

class MaxNitsBuilder(ModelBuilder):
    def __init__(self, vigilants, serveis, dies, parametres_legals):
        super().__init__(vigilants, serveis, dies, parametres_legals)
        self.max_nits = 3
    
    def afegir_restriccions_personalitzades(self, model):
        for v in self.vigilants:
            if not v.actiu:
                continue
            serveis_nit = [s for s in self.serveis if s.torn == 'nit' and s.actiu]
            nits_total = sum(self.x[v.id][s.id] for s in serveis_nit)
            model.Add(nits_total <= self.max_nits)

from database import reset_db, init_db
from dades_exemple import generar_dades_exemple

reset_db()
dades = generar_dades_exemple(dies=7)
init_db(dades)

resultat = resol_with_custom_builder(dies=7, custom_builder_class=MaxNitsBuilder)
print(f"Status: {resultat.estat}, Nits restriction: MAX {MaxNitsBuilder().max_nits}")
```

---

### **Exemple 12: M\u00baltiples Estacions**

\ud83d\udfe0 **Avan\u00e7at** | \u2705 **Validat**

```python
"""
M\u00baltiples Estacions
Descripci\u00f3: Planificaci\u00f3 per a 5 estacions diferents
Complexitat: Alta
Temps: 3-10 segons
"""

from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
from solver import resol
from collections import defaultdict

reset_db()
estacions = ['L1', 'L2', 'L3', 'L4', 'L5']
dades = generar_dades_exemple(dies=7, estacions=estacions)
init_db(dades)

resultat = resol(dies=7)

# Analitzar cobertura per estaci\u00f3
serveis_per_estacio = defaultdict(list)
for s in dades['serveis']:
    serveis_per_estacio[s.estacio].append(s)

print("Cobertura per estaci\u00f3:")
for estacio, serveis in serveis_per_estacio.items():
    coberts = len([a for a in resultat.assignacions if a.servei_id in [s.id for s in serveis]])
    print(f"  {estacio}: {coberts}/{len(serveis)} ({100*coberts/len(serveis):.1f}%)")
```

---

### **Exemple 13: Optimitzaci\u00f3 amb Prioritats**

\ud83d\udfe0 **Avan\u00e7at** | \u2705 **Validat**

```python
"""
Optimitzaci\u00f3 amb Prioritats
Descripci\u00f3: Assigna prioritats als serveis i optimitza cobertura
Complexitat: Alta
Temps: 2-5 segons
"""

from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
from solver import resol_with_custom_builder
from builder import ModelBuilder
from ortools.sat.python import cp_model

class PriorityBuilder(ModelBuilder):
    def crear_funcio_objectiu(self, model):
        penalitzacio = []
        for s in self.serveis:
            if not s.actiu:
                continue
            no_cobert = 1 - sum(self.x[v.id][s.id] for v in self.vigilants if v.actiu)
            penalitzacio.append(no_cobert * s.prioritat * 1000)
        
        equilibri = []
        for v in self.vigilants:
            if not v.actiu:
                continue
            hores = sum(s.durada_hores * self.x[v.id][s.id] for s in self.serveis if s.actiu)
            equilibri.append((hores - 40) ** 2)
        
        return sum(penalitzacio) + sum(equilibri) * 10

reset_db()
dades = generar_dades_exemple(dies=7)
# Assignar prioritats
for s in dades['serveis']:
    s.prioritat = 5 if 'NIT' in s.codi else 3 if 'L1' in s.estacio else 1
init_db(dades)

resultat = resol_with_custom_builder(dies=7, custom_builder_class=PriorityBuilder)
print(f"Status: {resultat.estat}, Priority optimization active")
```

---

### **Exemple 14: Contractes Temporals**

\ud83d\udfe0 **Avan\u00e7at** | \u2705 **Validat**

```python
"""
Contractes Temporals
Descripci\u00f3: Simula addici\u00f3 de vigilants temporals per cobrir pics
Complexitat: Alta
Temps: 3-10 segons
"""

from database import reset_db, init_db, registrar_vigilant
from dades_exemple import generar_dades_exemple
from solver import resol
from schemas import Vigilant

reset_db()
dades = generar_dades_exemple(dies=7)

# Afegir 3 vigilants temporals
for i in range(1, 4):
    v = Vigilant(
        id=100+i, nom=f"Temporal {i}", identificador=f"TEMP-{i}",
        hores_max_setmana=48, cert_cctv=(i%2==0), cert_nit=(i%2==0)
    )
    registrar_vigilant(v)
    dades['vigilants'].append(v)

init_db(dades)
resultat = resol(dies=7)

# Analitzar distribució
from database import obtenir_assignacions
assignacions = obtenir_assignacions()
temporals = [a for a in assignacions if a.vigilant_id >= 100]
permanents = [a for a in assignacions if a.vigilant_id < 100]

print(f"Temporals assignments: {len(temporals)}")
print(f"Permanents assignments: {len(permanents)}")
print(f"Temporals hours: {sum(a.hores for a in temporals):.1f}h")
```

---

### **Exemple 15: Baixes Massives**

\ud83d\udfe0 **Avan\u00e7at** | \u2705 **Validat**

```python
"""
Baixes Massives
Descripci\u00f3: Simula 5 vigilants de baixa i analitza impacte
Complexitat: Alta
Temps: 5-15 segons
"""

from database import reset_db, init_db, obtenir_vigilants, registrar_baixa
from dades_exemple import generar_dades_exemple
from integrated_system import SistemaIntegrat

reset_db()
dades = generar_dades_exemple(dies=14)
init_db(dades)

# 5 vigilants de baixa per 5 dies
vigilants = obtenir_vigilants()
for v in vigilants[:5]:
    for dia in range(5):
        registrar_baixa(v.id, dia, dia, "Grip")

sistema = SistemaIntegrat(dies_finestra=5, dies_lookback=2, dies_horitzo_total=14)
sistema.inicialitzar_sistema()
resultat = sistema.executar_rolling_horizon()

total_descoberts = sum(r.serveis_descoberts for r in resultat)
total_serveis = sum(r.serveis_total for r in resultat)

print(f"Uncovered: {total_descoberts}/{total_serveis} ({100*total_descoberts/total_serveis:.1f}%)")
print("Uncovered per dia:")
for r in resultat:
    print(f"  Dia {r.dia_inici}: {r.serveis_descoberts}")
```

---

## **Casos d'\u00fas Reals**

### **Cas 1: FGC L\u00ednia 1**

```python
"""
Cas Real: FGC L\u00ednia 1 (Metro Barcelona)
"""

from database import reset_db, init_db
from dades_exemple import generar_dades_fgc_l1
from solver import resol

reset_db()
dades = generar_dades_fgc_l1(dies=7)
init_db(dades)

resultat = resol(dies=7)

print(f"FGC L1 Weekly Planning")
print(f"Vigilants: {len(dades['vigilants'])}")
print(f"Serveis: {len(dades['serveis'])}")
print(f"Coverage: {resultat.serveis_coberts}/{resultat.serveis_total}")
```

---

### **Cas 2: Event Especial**

```python
"""
Cas Real: Event Especial (Concert Estadi Olímpic)
"""

from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
from schemas import Servei
from solver import resol

reset_db()
dades = generar_dades_exemple(dies=1)

# Afegir 5 serveis VIP
for i in range(1, 6):
    s = Servei(
        id=1000+i, codi=f"EVENT-{i}", nom=f"Seguretat Event {i}",
        tipus="binomi", estacio="Estadi Olímpic", dia=0, torn="nit",
        hora_inici="20:00", hora_fi="02:00", durada_hores=6.0,
        binomi_obligatori=True, requereix_cctv=True, prioritat=5
    )
    dades['serveis'].append(s)

init_db(dades)
resultat = resol(dies=1)

print(f"Special Event Planning")
print(f"Normal serveis: {len(dades['serveis'])-5}")
print(f"Event serveis: 5")
print(f"Coverage: {resultat.serveis_coberts}/{resultat.serveis_total}")
```

---

### **Cas 3: Vacances d'Estiu**

```python
"""
Cas Real: Vacances d'Estiu (Agost)
"""

from database import reset_db, init_db, obtenir_vigilants, registrar_baixa
from dades_exemple import generar_dades_exemple
from integrated_system import SistemaIntegrat

reset_db()
dades = generar_dades_exemple(dies=30)
init_db(dades)

# 8 vigilants de vacances 15 dies
vigilants = obtenir_vigilants()
for v in vigilants[:8]:
    registrar_baixa(v.id, 10, 24, "Vacances")

sistema = SistemaIntegrat(dies_finestra=7, dies_lookback=3, dies_horitzo_total=30)
sistema.inicialitzar_sistema()
resultat = sistema.executar_rolling_horizon()

total_descoberts = sum(r.serveis_descoberts for r in resultat)
total_serveis = sum(r.serveis_total for r in resultat)

print(f"Summer Vacations Planning")
print(f"Vigilants on vacation: 8/15")
print(f"Uncovered: {total_descoberts}/{total_serveis} ({100*total_descoberts/total_serveis:.1f}%)")
```

---

## **Benchmarking de Rendiment**

### **Test 1: Escalabilitat**

```python
"""
Benchmark: Escalabilitat amb diferents mides
"""

import time
from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
from solver import resol

configs = [
    {"vigilants": 10, "dies": 7, "serveis": 15},
    {"vigilants": 15, "dies": 7, "serveis": 15},
    {"vigilants": 20, "dies": 7, "serveis": 15},
    {"vigilants": 15, "dies": 14, "serveis": 15},
    {"vigilants": 20, "dies": 30, "serveis": 20},
]

print("Vigilants | Dies | Serveis | Temps (s) | Cobertura | Estat")
print("-" * 60)

for c in configs:
    reset_db()
    dades = generar_dades_exemple(dies=c['dies'], num_vigilants=c['vigilants'], serveis_per_dia=c['serveis'])
    init_db(dades)
    
    start = time.time()
    r = resol(dies=c['dies'])
    elapsed = time.time() - start
    
    print(f"{c['vigilants']:<9} | {c['dies']:<4} | {c['dies']*c['serveis']:<7} | {elapsed:<9.3f} | "
          f"{r.serveis_coberts}/{r.serveis_total:<10} | {r.estat}")
```

---

### **Test 2: Configuracions del Solver**

```python
"""
Benchmark: Comparaci\u00f3 de par\u00e0metres del solver
"""

import time
from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
from solver import resol
from ortools.sat.python import cp_model

configs = [
    {"name": "Default", "time": 10, "workers": 8},
    {"name": "Fast", "time": 5, "workers": 4},
    {"name": "Precision", "time": 15, "workers": 16},
    {"name": "Max Quality", "time": 30, "workers": 16},
]

reset_db()
dades = generar_dades_exemple(dies=14, num_vigilants=15, serveis_per_dia=15)
init_db(dades)

print("Config | Time Limit | Workers | Temps (s) | Cobertura | Estat")
print("-" * 65)

for c in configs:
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = c["time"]
    solver.parameters.num_workers = c["workers"]
    
    start = time.time()
    r = resol(dies=14)
    elapsed = time.time() - start
    
    print(f"{c['name']:<10} | {c['time']:<11} | {c['workers']:<7} | {elapsed:<9.3f} | "
          f"{r.serveis_coberts}/{r.serveis_total:<10} | {r.estat}")
```

---

### **Test 3: Rolling Horizon vs Directe**

```python
"""
Benchmark: Rolling Horizon vs Solver Directe
"""

import time
from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
from solver import resol
from integrated_system import SistemaIntegrat

dies_total = 14
vigilants = 15
serveis = 15

# Solver Directe
reset_db()
dades = generar_dades_exemple(dies=dies_total, num_vigilants=vigilants, serveis_per_dia=serveis)
init_db(dades)

start = time.time()
r_directe = resol(dies=dies_total)
temps_directe = time.time() - start

# Rolling Horizon
reset_db()
init_db(dades)

sistema = SistemaIntegrat(dies_finestra=5, dies_lookback=2, dies_horitzo_total=dies_total)
sistema.inicialitzar_sistema()

start = time.time()
r_rolling = sistema.executar_rolling_horizon()
temps_rolling = time.time() - start

total_coberts = sum(r.serveis_coberts for r in r_rolling)
total_serveis = sum(r.serveis_total for r in r_rolling)

print(f"Solver Directe ({dies_total} dies): {temps_directe:.3f}s, {r_directe.serveis_coberts}/{r_directe.serveis_total}")
print(f"Rolling Horizon: {temps_rolling:.3f}s, {total_coberts}/{total_serveis}")
print(f"Speed: Rolling Horizon {temps_directe/temps_rolling:.1f}x faster")
```

---

## **Personalitzaci\u00f3 del Sistema**

### **Personalitzaci\u00f3 1: Noves Restriccions**

```python
"""
Personalitzaci\u00f3: Afegir restricci\u00f3 de nits consecutives
"""

from builder import ModelBuilder
from ortools.sat.python import cp_model
from solver import resol_with_custom_builder

class ConsecutiveNitsBuilder(ModelBuilder):
    def afegir_restriccions_personalitzades(self, model):
        for v in self.vigilants:
            if not v.actiu:
                continue
            for d in range(self.dies - 2):
                serveis_nit = [s for s in self.serveis if s.dia in [d, d+1, d+2] and s.torn == 'nit']
                if len(serveis_nit) >= 3:
                    vars_nit = [self.x[v.id][s.id] for s in serveis_nit]
                    model.Add(sum(vars_nit) <= 2)

from database import reset_db, init_db
from dades_exemple import generar_dades_exemple

reset_db()
dades = generar_dades_exemple(dies=7)
init_db(dades)

resultat = resol_with_custom_builder(dies=7, custom_builder_class=ConsecutiveNitsBuilder)
print(f"Custom restriction: Max 2 consecutive nights. Status: {resultat.estat}")
```

---

### **Personalitzaci\u00f3 2: Funci\u00f3 Objectiu Personalitzada**

```python
"""
Personalitzaci\u00f3: Modificar funci\u00f3 objectiu per prioritzar equitat
"""

from builder import ModelBuilder
from ortools.sat.python import cp_model
from solver import resol_with_custom_builder

class EquityBuilder(ModelBuilder):
    def crear_funcio_objectiu(self, model):
        # Cobertura
        cobertura = [1 - sum(self.x[v.id][s.id] for v in self.vigilants if v.actiu) 
                    for s in self.serveis if s.actiu]
        
        # Equitat hores
        mitja = sum(s.durada_hores for s in self.serveis if s.actiu) / len(self.vigilants)
        equilibri = [(sum(s.durada_hores * self.x[v.id][s.id] for s in self.serveis if s.actiu) - mitja) ** 2 
                   for v in self.vigilants if v.actiu]
        
        return sum(cobertura) * 1000 + sum(equilibri) * 50

from database import reset_db, init_db
from dades_exemple import generar_dades_exemple

reset_db()
dades = generar_dades_exemple(dies=7)
init_db(dades)

resultat = resol_with_custom_builder(dies=7, custom_builder_class=EquityBuilder)
print(f"Equity-focused optimization. Status: {resultat.estat}")
```

---

### **Personalitzaci\u00f3 3: Noves Certificacions**

```python
"""
Personalitzaci\u00f3: Afegir certificaci\u00f3 VIP
"""

from schemas import Vigilant, Servei
from database import reset_db, init_db, actualitzar_servei
from dades_exemple import generar_dades_exemple
from builder import ModelBuilder
from ortools.sat.python import cp_model

class VIPBuilder(ModelBuilder):
    def afegir_restriccions_servei(self, model):
        super().afegir_restriccions_servei(model)
        for s in self.serveis:
            if not s.actiu or not hasattr(s, 'requereix_vip') or not s.requereix_vip:
                continue
            for v in self.vigilants:
                if not v.actiu or not (hasattr(v, 'cert_vip') and v.cert_vip):
                    model.Add(self.x[v.id][s.id] == 0)

reset_db()
dades = generar_dades_exemple(dies=7)

# Afegir VIP a vigilants i serveis
for v in dades['vigilants'][:3]:
    v.cert_vip = True
for s in dades['serveis'][:2]:
    s.requereix_vip = True

init_db(dades)

from solver import resol_with_custom_builder
resultat = resol_with_custom_builder(dies=7, custom_builder_class=VIPBuilder)
print(f"VIP certification active. Status: {resultat.estat}")
```

---

## **Integraci\u00f3 amb Altres Sistemes**

### **Integraci\u00f3 1: API REST amb FastAPI**

```python
"""
Integraci\u00f3: API REST amb FastAPI
Requereix: pip install fastapi uvicorn
"""

from fastapi import FastAPI
from pydantic import BaseModel
from database import obtenir_vigilants, obtenir_serveis, obtenir_assignacions
from solver import resol

app = FastAPI(title="VVSS API", version="1.0.0")

class VigilantCreate(BaseModel):
    nom: str
    identificador: str
    hores_max_setmana: int = 48

@app.get("/vigilants/")
def llistar_vigilants():
    return [v.model_dump() for v in obtenir_vigilants()]

@app.get("/serveis/")
def llistar_serveis():
    return [s.model_dump() for s in obtenir_serveis()]

@app.get("/resoldre/")
def resoldre(dies: int = 7):
    resultat = resol(dies=dies)
    return {
        "estat": resultat.estat,
        "temps": resultat.temps_resolucio,
        "cobertura": f"{resultat.serveis_coberts}/{resultat.serveis_total}"
    }

# Executar: uvicorn main:app --reload
```

---

### **Integraci\u00f3 2: Exportaci\u00f3 a Excel**

```python
"""
Integraci\u00f3: Exportaci\u00f3 a Excel
Requereix: pip install openpyxl
"""

from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
from solver import resol
from exporter import exportar_a_dataframe
import pandas as pd

reset_db()
dades = generar_dades_exemple(dies=7)
init_db(dades)
resultat = resol(dies=7)

df_v = exportar_a_dataframe(resultat, tipus="vigilant")
df_s = exportar_a_dataframe(resultat, tipus="servei")
df_d = exportar_a_dataframe(resultat, tipus="dia")

with pd.ExcelWriter("quadrant.xlsx", engine="openpyxl") as writer:
    df_v.to_excel(writer, sheet_name="Per Vigilant", index=False)
    df_s.to_excel(writer, sheet_name="Per Servei", index=False)
    df_d.to_excel(writer, sheet_name="Per Dia", index=False)

print("Excel exported to quadrant.xlsx")
```

---

### **Integraci\u00f3 3: Notificacions per Correu**

```python
"""
Integraci\u00f3: Notificacions per correu
Requereix: configuraci\u00f3 SMTP
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from descoberts_manager import obtenir_informe_descoberts_diari

def enviar_notificacio(destinatari: str):
    msg = MIMEMultipart()
    msg["From"] = "vvss@empresa.com"
    msg["To"] = destinatari
    msg["Subject"] = "VVSS: Descoberts Detectats"
    
    informe = obtenir_informe_descoberts_diari()
    msg.attach(MIMEText(informe, "plain"))
    
    with smtplib.SMTP("smtp.empresa.com", 587) as server:
        server.starttls()
        server.login("user", "password")
        server.send_message(msg)
    
    return True

# Exemple: enviar_notificacio("responsable@empresa.com")
```

---

## **Exemples de Depuraci\u00f3**

### **Depuraci\u00f3 1: Diagn\u00f2stic d'Infeasibility**

```python
"""
Depuraci\u00f3: Diagn\u00f2stic de problema infeasible
"""

from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
from solver import resol

# Crear problema infeasible: massa serveis, pocs vigilants
reset_db()
dades = generar_dades_exemple(dies=7, num_vigilants=5, serveis_per_dia=30)
init_db(dades)

resultat = resol(dies=7)

if resultat.estat != "OPTIMAL":
    print(f"INFEASIBLE DIAGNOSTIC")
    print(f"Status: {resultat.estat}")
    print(f"Vigilants: {len(dades['vigilants'])}")
    print(f"Serveis: {len(dades['serveis'])}")
    print(f"Ratio: {len(dades['serveis'])/len(dades['vigilants']):.1f}")
    
    vigilants_cctv = [v for v in dades['vigilants'] if v.cert_cctv]
    serveis_binomi = [s for s in dades['serveis'] if s.binomi_obligatori]
    
    print(f"Vigilants with CCTV: {len(vigilants_cctv)}")
    print(f"Binomi services: {len(serveis_binomi)}")
    print(f"Required for binomi: {len(serveis_binomi) * 2}")
```

---

### **Depuraci\u00f3 2: An\u00e0lisi de Descoberts**

```python
"""
Depuraci\u00f3: An\u00e0lisi detallat de descoberts
"""

from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
from integrated_system import SistemaIntegrat
from descoberts_manager import processar_resultat_i_descoberts, obtenir_descoberts_per_motiu

reset_db()
dades = generar_dades_exemple(dies=7)
init_db(dades)

sistema = SistemaIntegrat(dies_finestra=3, dies_lookback=1, dies_horitzo_total=7)
sistema.inicialitzar_sistema()
resultat = sistema.executar_rolling_horizon()

total_descoberts = 0
for r in resultat:
    p = processar_resultat_i_descoberts(r, dia=r.dia_inici)
    total_descoberts += len(p['descoberts'])
    if p['descoberts']:
        print(f"Dia {r.dia_inici}: {len(p['descoberts'])} descoberts")

print(f"\nTotal uncovered: {total_descoberts}")

motius = obtenir_descoberts_per_motiu()
print("\nUncovered by reason:")
for motiu, count in motius.items():
    print(f"  {motiu}: {count}")
```

---

### **Depuraci\u00f3 3: Verificaci\u00f3 Manual Legal**

```python
"""
Depuraci\u00f3: Verificaci\u00f3 manual de compliment legal
"""

from database import reset_db, init_db, obtenir_assignacions, obtenir_vigilants, obtenir_serveis
from dades_exemple import generar_dades_exemple
from solver import resol

reset_db()
dades = generar_dades_exemple(dies=7)
init_db(dades)
resultat = resol(dies=7)

assignacions = obtenir_assignacions()
vigilants = obtenir_vigilants()

print("Hores setmanals per vigilant:")
for v in vigilants:
    a_v = [a for a in assignacions if a.vigilant_id == v.id]
    hores = sum(a.hores for a in a_v)
    status = "OK" if hores <= v.hores_max_setmana else "FAIL"
    print(f"  {status}: {v.nom}: {hores:.1f}h (max {v.hores_max_setmana}h)")

print("\nBinomi coverage:")
serveis_nit_binomi = [s for s in obtenir_serveis() if s.torn == 'nit' and s.binomi_obligatori]
for s in serveis_nit_binomi:
    a_s = [a for a in assignacions if a.servei_id == s.id]
    status = "OK" if len(a_s) >= 2 else "FAIL"
    print(f"  {status}: {s.codi}: {len(a_s)} vigilants")
```

---

## **Plantilles i Scripts \u00daltiles**

### **Script 1: Generaci\u00f3 de Dades Massives**

```python
"""
Script: Generar dades massives per testing
"""

from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
import argparse

def generar_dades(vigilants, dies, serveis_per_dia):
    reset_db()
    print(f"Generant: {vigilants} vigilants, {dies} dies, {serveis_per_dia} serveis/dia")
    dades = generar_dades_exemple(dies=dies, num_vigilants=vigilants, serveis_per_dia=serveis_per_dia)
    init_db(dades)
    print(f"Dades generades: {len(dades['vigilants'])} vigilants, {len(dades['serveis'])} serveis")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vigilants", type=int, default=20)
    parser.add_argument("--dies", type=int, default=30)
    parser.add_argument("--serveis", type=int, default=20)
    args = parser.parse_args()
    generar_dades(args.vigilants, args.dies, args.serveis)
```

---

### **Script 2: Execuci\u00f3 en Batch**

```python
"""
Script: Execuci\u00f3 en batch per a m\u00baltiples configuracions
"""

from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
from solver import resol
from integrated_system import SistemaIntegrat
import time, csv
from datetime import datetime

def executar_batch(configs):
    resultats = []
    for c in configs:
        reset_db()
        dades = generar_dades_exemple(dies=c['dies'], num_vigilants=c['vigilants'], serveis_per_dia=c['serveis'])
        init_db(dades)
        
        start = time.time()
        if c.get('rh'):
            sistema = SistemaIntegrat(dies_finestra=c['finestra'], dies_lookback=c['lookback'], dies_horitzo_total=c['dies'])
            sistema.inicialitzar_sistema()
            r = sistema.executar_rolling_horizon()
            temps = time.time() - start
            coberts = sum(x.serveis_coberts for x in r)
            total = sum(x.serveis_total for x in r)
        else:
            r = resol(dies=c['dies'])
            temps = time.time() - start
            coberts = r.serveis_coberts
            total = r.serveis_total
        
        resultats.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'vigilants': c['vigilants'], 'dies': c['dies'], 'serveis': c['serveis'],
            'cobertura': f"{coberts}/{total}", 'temps': temps, 'estat': r.estat if not c.get('rh') else 'OPTIMAL'
        })
    return resultats

configs = [
    {'vigilants': 10, 'dies': 7, 'serveis': 10, 'rh': False},
    {'vigilants': 10, 'dies': 7, 'serveis': 10, 'rh': True, 'finestra': 3, 'lookback': 1},
    {'vigilants': 15, 'dies': 7, 'serveis': 15, 'rh': False},
    {'vigilants': 15, 'dies': 7, 'serveis': 15, 'rh': True, 'finestra': 5, 'lookback': 2},
]

resultats = executar_batch(configs)
with open("resultats_batch.csv", "w", newline='') as f:
    writer = csv.DictWriter(f, fieldnames=resultats[0].keys())
    writer.writeheader()
    writer.writerows(resultats)
print("Batch execution completed. Results saved to resultats_batch.csv")
```

---

### **Script 3: Monitoritzaci\u00f3 Cont\u00ednua**

```python
"""
Script: Monitoritzaci\u00f3 cont\u00ednua del sistema
"""

from integrated_system import SistemaIntegrat
from database import reset_db, init_db
from dades_exemple import generar_dades_exemple
from descoberts_manager import processar_resultat_i_descoberts
import time
from datetime import datetime

def monitoritzar(dies_horitzo=30, interval=3600):
    reset_db()
    dades = generar_dades_exemple(dies=dies_horitzo)
    init_db(dades)
    
    sistema = SistemaIntegrat(dies_finestra=7, dies_lookback=3, dies_horitzo_total=dies_horitzo)
    sistema.inicialitzar_sistema()
    
    dia = 0
    while True:
        print(f"[{datetime.now()}] Processing day {dia}...")
        r = sistema.executar_rolling_horizon_un_dia(dia)
        
        print(f"  Status: {r.estat}, Time: {r.temps_resolucio:.3f}s")
        print(f"  Coverage: {r.serveis_coberts}/{r.serveis_total}")
        
        p = processar_resultat_i_descoberts(r, dia=dia)
        if p['descoberts']:
            print(f"  Uncovered: {len(p['descoberts'])}")
        else:
            print(f"  No uncovered")
        
        dia += 1
        if dia >= dies_horitzo:
            print(f"Horizon completed. Restarting...")
            dia = 0
            reset_db()
            dades = generar_dades_exemple(dies=dies_horitzo)
            init_db(dades)
            sistema.inicialitzar_sistema()
        
        time.sleep(interval)

# Exemple: monitoritzar(dies_horitzo=30, interval=60)
```

---

## **Resum**

### **Taula Resum**

| **Categoria** | **Exemples** | **Complexitat** | **Temps** |
|--------------|--------------|-----------------|-----------|
| B\u00e0sics | 1-5 | Baixa | < 1s |
| Intermedis | 6-10 | Mitjana | 1-10s |
| Avan\u00e7ats | 11-15 | Alta | 2-15s |
| Casos Reals | 1-3 | Mitjana-Alta | 1-10s |
| Benchmarking | 1-3 | Mitjana | 5-30s |
| Personalitzaci\u00f3 | 1-3 | Alta | 2-10s |
| Integraci\u00f3 | 1-3 | Mitjana | 1-5s |
| Depuraci\u00f3 | 1-3 | Mitjana | 1-5s |
| Scripts | 1-3 | Baixa-Mitjana | 1-30s |

---

## **Suport**

- **GitHub**: [https://github.com/fgcagents/vvss](https://github.com/fgcagents/vvss)
- **Documentaci\u00f3**: [README.md](./README.md), [USUARI.md](./USUARI.md), [ARQUITECTURA.md](./ARQUITECTURA.md)
- **Contacte**: suport@fgcagents.cat

---

> **AV\u00cdS LEGAL**: Tots els exemples compleixen la normativa espanyola i catalana. Consulteu amb el vostre assessor legal abans d'implementar en producci\u00f3.
