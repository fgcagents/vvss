"""
Motor CP-SAT per a l'assignacio de vigilants de seguretat a serveis
d'una xarxa ferroviaria de transport de passatgers.

Aquest fitxer ara és un wrapper que importa des de schemas.py, builder.py i solver.py
per a mantenir compatibilitat amb el codi existent (rolling_horizon_demo.py, urgencia.py).

Per a nous projectes, utilitzeu directament:
  from schemas import Vigilant, Servei, ParametresLegals, Resultat
  from solver import resol, valida_resultat
  from builder import ModelBuilder

Pensat com una capa especialitzada sobre el mateix enfocament que ja
feieu servir a Xivato (prioritat per hores acumulades, preferencia de
zona/torn), pero afegint-hi les restriccions dures propies del sector
de seguretat privada:

  1. Habilitacio (TIP) i categoria: nomes es pot cobrir un servei si
     el vigilant te la categoria requerida (armat / no armat / CCTV).
  2. Descans minim legal entre jornades (conveni estatal de seguretat:
     13h amb caracter general, 12h per a auxiliars de serveis; en
     serveis de 24h moltes empreses apliquen descansos compensatoris
     molt mes llargs via pacte d'empresa -- veure README, es un
     parametre configurable, NO un valor legal universal).
  3. Jornada maxima setmanal i objectiu d'hores anuals.
  4. Descans setmanal obligatori (com a minim un dia lliure/setmana).
  5. Cobertura minima simultania per lloc/torn (nombre de vigilants).

L'objectiu combina (igual que al motor "per prioritats" de Xivato):
  - Minimitzar la desviacio respecte de l'objectiu d'hores de cada
    vigilant (qui te menys hores acumulades te prioritat).
  - Maximitzar el compliment de preferencies de zona/torn com a criteri
    secundari.
  - Equitat en distribució de torns no desitjats (nits).
"""

# Re-exporta tot des de schemas, builder i solver per a compatibilitat
from schemas import Vigilant, Servei, ParametresLegals, Resultat
from solver import resol, valida_resultat
from builder import ModelBuilder

# Manté l'antic nom de la funció _descans_requerit per a compatibilitat
from builder import _descans_requerit

# Alias per a compatibilitat amb codi existent
resol_antic = resol  # Funció original amb tots els paràmetres

__all__ = [
    "Vigilant",
    "Servei", 
    "ParametresLegals",
    "Resultat",
    "resol",
    "valida_resultat",
    "ModelBuilder",
    "_descans_requerit",
]
