"""Selecció de substituts per a serveis que necessiten cobertura immediata."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from schemas import ParametresLegals, Servei, Vigilant
from builder import _descans_requerit


@dataclass(frozen=True)
class CandidatSubstitucio:
    vigilant_id: str
    hores_acumulades: float
    motiu_descart: Optional[str] = None


def _se_solapen(a: Servei, b: Servei) -> bool:
    return a.inici < b.fi and b.inici < a.fi


def troba_substitut(
    servei: Servei,
    vigilants: list[Vigilant],
    serveis_ja_assignats: dict[str, list[Servei]],
    params: ParametresLegals,
) -> tuple[Optional[str], list[CandidatSubstitucio]]:
    """Retorna el candidat vàlid amb menys hores acumulades.

    La llista retornada inclou també els candidats descartats per facilitar
    l'auditoria de les decisions d'urgència.
    """
    candidats: list[CandidatSubstitucio] = []
    candidats_valids: list[CandidatSubstitucio] = []

    for vigilant in vigilants:
        motiu: Optional[str] = None
        serveis = serveis_ja_assignats.get(vigilant.id, [])
        if not vigilant.actiu:
            motiu = "vigilant inactiu"
        elif servei.habilitacio_requerida not in vigilant.habilitacions:
            motiu = "habilitació no disponible"
        elif any(
            not (servei.fi <= inici or servei.inici >= fi)
            for inici, fi in vigilant.baixes
        ):
            motiu = "vigilant de baixa"
        elif any(_se_solapen(servei, assignat) for assignat in serveis):
            motiu = "solapament temporal"
        else:
            for assignat in sorted(serveis, key=lambda s: s.inici):
                if assignat.fi <= servei.inici:
                    gap = (servei.inici - assignat.fi).total_seconds() / 3600
                    if gap < _descans_requerit(assignat, params):
                        motiu = "descans insuficient abans del servei"
                        break
                elif servei.fi <= assignat.inici:
                    gap = (assignat.inici - servei.fi).total_seconds() / 3600
                    if gap < _descans_requerit(servei, params):
                        motiu = "descans insuficient després del servei"
                        break
            if motiu is None:
                hores_setmana = sum(
                    s.durada_hores
                    for s in serveis
                    if s.inici.isocalendar()[:2] == servei.inici.isocalendar()[:2]
                )
                if hores_setmana + servei.durada_hores > vigilant.hores_max_setmana:
                    motiu = "supera el màxim setmanal"

        candidat = CandidatSubstitucio(
            vigilant_id=vigilant.id,
            hores_acumulades=vigilant.hores_acumulades,
            motiu_descart=motiu,
        )
        candidats.append(candidat)
        if motiu is None:
            candidats_valids.append(candidat)

    candidats.sort(key=lambda c: (c.motiu_descart is not None, c.hores_acumulades, c.vigilant_id))
    millor = min(candidats_valids, key=lambda c: (c.hores_acumulades, c.vigilant_id), default=None)
    return (millor.vigilant_id if millor else None), candidats
