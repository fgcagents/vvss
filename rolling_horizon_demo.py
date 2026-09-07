"""
Demostracio d'horitzo mobil (5 dies, es publica dia a dia), inspirada en
l'article de L-RHO (MIT) que vau compartir: en lloc de re-resoldre cada
finestra des de zero, es reutilitza la informacio de la resolucio anterior
de dues maneres:

  1. `assignacions_fixades` -- el dia que ja s'ha PUBLICAT es fixa com a
     restriccio dura. Aixo inclou tambe 1-2 dies de "look-back" abans de
     la finestra actual, perque les restriccions de descans (gap entre
     torns + finestra mobil de 7 dies) puguin veure el que ja s'ha
     treballat just abans de la finestra -- si no, el solver podria
     "oblidar" un torn de nit ahir i planificar un mati massa d'hora avui.
  2. `pistes_calents` -- els dies encara TEMPTATIUS (dins la finestra pero
     no publicats) de l'ultima resolucio es passen com a hint via
     `model.AddHint()`. No obliguen res, pero acceleren la cerca i
     redueixen el "churn" de zona/torn respecte de la resolucio anterior
     -- exactament el compromis que vau trobar entre els lots V31/V32 i
     V34/V35/V36 (equilibri d'hores vs. canvis de zona/torn).

Aixo NO es una implementacio de L-RHO complet (no hi ha cap model de
machine learning que decideixi que congelar) -- es una versio heuristica
senzilla: "congela el que ja esta publicat, dona pistes de la resta".
Vegeu el README per a com evolucionar-ho cap a una versio amb ML real
si en el futur teniu prou historial de resolucions.
"""

from datetime import timedelta

from dades_exemple import genera_vigilants
from model import ParametresLegals, Servei, Vigilant, resol
from dades_exemple import genera_serveis as _genera_base


DIES_FINESTRA = 5
DIES_LOOKBACK = 2
DIES_HORITZO_TOTAL = 12


def main():
    vigilants = genera_vigilants()
    tots_els_serveis = {s.id: s for s in _genera_base(dies=DIES_HORITZO_TOTAL)}
    params = ParametresLegals()

    publicat: dict[tuple[str, str], int] = {}      # (vigilant_id, servei_id) -> 1
    tentatiu_anterior: dict[tuple[str, str], int] = {}
    hores_publicades: dict[str, float] = {v.id: v.hores_acumulades for v in vigilants}

    print(f"{'Dia':>4} | {'Estat':<9} | {'Temps fred':>11} | {'Temps calent':>13} | Servei publicat avui")
    print("-" * 80)

    for dia_publicar in range(DIES_HORITZO_TOTAL - DIES_FINESTRA + 1):
        dia_lookback_inici = max(0, dia_publicar - DIES_LOOKBACK)
        serveis_finestra = [
            s for s in tots_els_serveis.values()
            if dia_lookback_inici <= _dia_index(s) < dia_publicar + DIES_FINESTRA
        ]

        # Assignacions que ja son historia fixa (look-back + tot el que s'ha
        # publicat fins ara i cau dins la finestra -- normalment nomes el look-back).
        fixades = {
            (v_id, s_id): valor
            for (v_id, s_id), valor in publicat.items()
            if s_id in {s.id for s in serveis_finestra}
        }

        vigilants_actualitzats = _amb_hores_actualitzades(vigilants, hores_publicades)

        # --- Resolucio "calenta": amb pistes de l'ultima resolucio tentativa ---
        resultat_calent = resol(
            vigilants_actualitzats, serveis_finestra, params,
            assignacions_fixades=fixades, pistes_calents=tentatiu_anterior,
        )

        # --- Resolucio "freda": el mateix problema, sense pistes (nomes per comparar) ---
        resultat_fred = resol(
            vigilants_actualitzats, serveis_finestra, params,
            assignacions_fixades=fixades, pistes_calents=None,
        )

        # Publiquem nomes el primer dia de la finestra (dia_publicar)
        serveis_avui = [s for s in serveis_finestra if _dia_index(s) == dia_publicar]
        ids_avui = {s.id for s in serveis_avui}
        assignats_avui = [(v, s) for v, s in resultat_calent.assignacions if s in ids_avui]

        for v_id, s_id in assignats_avui:
            publicat[v_id, s_id] = 1
            hores_publicades[v_id] = hores_publicades.get(v_id, 0.0) + tots_els_serveis[s_id].durada_hores

        # Els dies que queden tentatius (dins la finestra pero encara no publicats)
        tentatiu_anterior = {
            (v, s): 1 for v, s in resultat_calent.assignacions if s not in ids_avui
        }

        print(
            f"{dia_publicar:>4} | {resultat_calent.estat:<9} | "
            f"{resultat_fred.temps_resolucio_segons:>9.3f} s | "
            f"{resultat_calent.temps_resolucio_segons:>11.3f} s | "
            f"{len(assignats_avui)} assignacions"
        )
        if resultat_calent.avisos:
            for a in resultat_calent.avisos:
                print(f"      avis: {a}")

    print("\nHores publicades finals per vigilant:")
    for v in vigilants:
        print(f"  {v.id}: {hores_publicades[v.id]:.1f}h")


def _dia_index(s: Servei) -> int:
    # dades_exemple.py numera els serveis amb "-{dia}" al final de l'id
    return int(s.id.rsplit("-", 1)[1])


def _amb_hores_actualitzades(vigilants: list[Vigilant], hores: dict[str, float]) -> list[Vigilant]:
    actualitzats = []
    for v in vigilants:
        nou = Vigilant(**{**v.__dict__, "hores_acumulades": hores.get(v.id, v.hores_acumulades)})
        actualitzats.append(nou)
    return actualitzats


if __name__ == "__main__":
    main()
