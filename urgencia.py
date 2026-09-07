"""
Heuristic per a SUBSTITUCIONS D'URGENCIA -- nomes per a aquest cas concret
(algu truca malalt i cal cobrir un servei ja, no en 30 segons d'una
resolucio completa de CP-SAT). NO es fa servir per a planificacio continua
-- aixo segueix sent, sempre, `model.resol()`.

Regla d'or d'aquest fitxer: no reimplementa cap restriccio legal propia.
Reutilitza `compatible_temporalment()` de model.py per al descans i les
mateixes comprovacions d'habilitacio/actiu -- una unica font de veritat
sobre que es legal, compartida amb el CP-SAT. Si mai calgues canviar el
descans minim o afegir una nova categoria, nomes es toca a `model.py`.

Criteri d'equitat: entre tots els candidats VALIDS (habilitacio correcta +
no trenca descans amb res que ja tingui assignat), es tria qui tingui
MENYS hores acumulades -- el mateix criteri que ja fa servir la funcio
objectiu del CP-SAT. Aixo no fa que l'heuristic sigui "just" en sentit
global (nomes decideix un servei, no re-equilibra res mes), pero
GARANTEIX que no vagi sistematicament en contra de l'equitat: si sempre
tries qui te menys hores, en el pitjor cas ets neutre respecte de
l'equilibri, mai el destrueixes.

Despres de triar, cal SEMPRE:
  1. Publicar aquesta assignacio concreta (afegir-la a `assignacions_fixades`
     de la propera crida a `resol()`).
  2. Actualitzar `hores_acumulades` del vigilant triat.
  3. Deixar que la propera resolucio d'horitzo mobil continui equilibrant
     a partir d'aqui. L'heuristic no "sap" res d'equilibri a llarg termini
     -- nomes evita que la substitucio d'urgencia el trenqui mes del compte.
"""

from __future__ import annotations

from dataclasses import dataclass

from model import ParametresLegals, Servei, Vigilant, compatible_temporalment


@dataclass
class CandidatUrgencia:
    vigilant_id: str
    hores_acumulades: float
    motiu_descart: str | None = None  # None == candidat valid


def troba_substitut(
    servei_urgent: Servei,
    vigilants: list[Vigilant],
    serveis_ja_assignats: dict[str, list[Servei]],  # vigilant_id -> els seus serveis (publicats o temptatius) que puguin xocar en el temps
    params: ParametresLegals,
) -> tuple[str | None, list[CandidatUrgencia]]:
    """Retorna (vigilant_id triat, o None si cap candidat es valid, tots els
    candidats avaluats amb el motiu de descart -- per poder mostrar-ho a qui
    gestiona la urgencia, no nomes un si/no opac)."""
    avaluats: list[CandidatUrgencia] = []

    for v in vigilants:
        if not v.actiu:
            avaluats.append(CandidatUrgencia(v.id, v.hores_acumulades, "inactiu (baixa/vacances)"))
            continue
        if servei_urgent.habilitacio_requerida not in v.habilitacions:
            avaluats.append(CandidatUrgencia(v.id, v.hores_acumulades, "no te l'habilitacio requerida"))
            continue

        conflicte_amb = next(
            (s for s in serveis_ja_assignats.get(v.id, [])
             if not compatible_temporalment(s, servei_urgent, params)),
            None,
        )
        if conflicte_amb:
            avaluats.append(CandidatUrgencia(
                v.id, v.hores_acumulades, f"trencaria el descans amb {conflicte_amb.id}"
            ))
            continue

        avaluats.append(CandidatUrgencia(v.id, v.hores_acumulades, None))

    valids = [c for c in avaluats if c.motiu_descart is None]
    if not valids:
        return None, avaluats  # cap candidat -- cal escalar a gestio manual (hores extra, empresa externa, etc.)

    triat = min(valids, key=lambda c: c.hores_acumulades)
    return triat.vigilant_id, avaluats


if __name__ == "__main__":
    # Demo: V02 truca malalt just abans del seu torn de tarda a Central.
    from datetime import datetime, timedelta
    from dades_exemple import genera_vigilants, genera_serveis

    vigilants = genera_vigilants()
    serveis = {s.id: s for s in genera_serveis(dies=1)}
    params = ParametresLegals()

    servei_urgent = serveis["CEN-tarda-0"]

    # Simulem que cadascu ja te el seu torn de mati assignat (dades d'exemple)
    serveis_ja_assignats = {
        "V01": [serveis["CEN-mati-0"]],
        "V04": [serveis["SUD-mati-0"]],
        "V08": [serveis["CEN-mati-0"]],
    }

    triat, avaluats = troba_substitut(servei_urgent, vigilants, serveis_ja_assignats, params)

    print(f"Servei urgent: {servei_urgent.id} ({servei_urgent.zona}, {servei_urgent.habilitacio_requerida})\n")
    for c in sorted(avaluats, key=lambda c: c.hores_acumulades):
        estat = "VALID" if c.motiu_descart is None else f"descartat: {c.motiu_descart}"
        marca = " <-- TRIAT" if c.vigilant_id == triat else ""
        print(f"  {c.vigilant_id}: {c.hores_acumulades:6.1f}h acumulades -- {estat}{marca}")

    print(f"\nSubstitut triat: {triat}")
