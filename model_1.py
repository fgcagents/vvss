"""
Motor CP-SAT per a l'assignacio de vigilants de seguretat a serveis
d'una xarxa ferroviaria de transport de passatgers.

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
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Optional

from ortools.sat.python import cp_model


# ---------------------------------------------------------------------------
# Model de dades
# ---------------------------------------------------------------------------

@dataclass
class Vigilant:
    id: str
    habilitacions: set[str]            # p.ex. {"no_armat"}, {"armat", "no_armat"}, {"cctv"}
    hores_objectiu_periode: float       # hores contractuals per al periode planificat
    hores_acumulades: float = 0.0       # hores ja fetes abans d'aquest periode
    hores_max_setmana: float = 48.0     # topall legal absolut
    zona_preferida: Optional[str] = None
    torn_preferit: Optional[str] = None # "mati" | "tarda" | "nit" | "24h"
    actiu: bool = True                  # False si esta de baixa/vacances tot el periode


@dataclass
class Servei:
    id: str
    zona: str                           # estacio, linia o tram
    inici: datetime
    fi: datetime
    habilitacio_requerida: str          # "armat" | "no_armat" | "cctv"
    vigilants_requerits: int = 1
    torn: Optional[str] = None          # etiqueta informativa: "mati"/"tarda"/"nit"/"24h"

    @property
    def durada_hores(self) -> float:
        return (self.fi - self.inici).total_seconds() / 3600.0


@dataclass
class ParametresLegals:
    """Parametres configurables -- ajusteu-los al conveni/pacte d'empresa real."""
    descans_minim_hores: float = 13.0
    descans_minim_auxiliars_hores: float = 12.0
    # Descans compensatori especial per a torns molt llargs (p.ex. serveis de 24h).
    # Si un servei dura >= llindar_torn_llarg_hores, el descans minim posterior
    # passa a ser descans_torn_llarg_hores en lloc del descans_minim_hores general.
    llindar_torn_llarg_hores: float = 20.0
    descans_torn_llarg_hores: float = 48.0
    dies_periode_descans_setmanal: int = 7  # cada X dies, com a minim 1 lliure


@dataclass
class Resultat:
    assignacions: list[tuple[str, str]]      # (vigilant_id, servei_id)
    hores_finals: dict[str, float]
    estat: str
    cobertura_incompleta: list[tuple[str, int, int]]  # (servei_id, coberts, requerits)
    avisos: list[str] = field(default_factory=list)
    temps_resolucio_segons: float = 0.0


# ---------------------------------------------------------------------------
# Construccio i resolucio del model
# ---------------------------------------------------------------------------

def _descans_requerit(servei_previ: Servei, params: ParametresLegals) -> float:
    if servei_previ.durada_hores >= params.llindar_torn_llarg_hores:
        return params.descans_torn_llarg_hores
    return params.descans_minim_hores


def resol(
    vigilants: list[Vigilant],
    serveis: list[Servei],
    params: ParametresLegals,
    pes_equilibri_hores: int = 10,
    pes_preferencia: int = 1,
    permetre_cobertura_parcial: bool = True,
    temps_maxim_segons: float = 30.0,
    assignacions_fixades: dict[tuple[str, str], int] | None = None,
    pistes_calents: dict[tuple[str, str], int] | None = None,
) -> Resultat:
    """
    assignacions_fixades: dies ja PUBLICATS -- es fixen com a restriccio dura
      (el solver no els pot tocar; qualsevol canvi ha de ser manual, com ja
      feieu). Format {(vigilant_id, servei_id): 0 o 1}.
    pistes_calents: assignacions TEMPTATIVES de l'ultima resolucio (dies dins
      la finestra de 5 dies pero encara no publicats) que es passen com a
      "hint" al solver -- no obliga res, nomes li diu per on començar a
      buscar. Redueix el "churn" de zona/torn entre resolucions successives
      sense sacrificar l'equilibri d'hores (vegeu README, seccio inspirada
      en l'article de L-RHO/MIT sobre rolling-horizon optimization).
    """
    model = cp_model.CpModel()
    serveis = sorted(serveis, key=lambda s: s.inici)

    # --- Variables de decisio: x[v.id, s.id] = 1 si el vigilant v cobreix el servei s
    x: dict[tuple[str, str], cp_model.IntVar] = {}
    for v in vigilants:
        if not v.actiu:
            continue
        for s in serveis:
            if s.habilitacio_requerida in v.habilitacions:
                x[v.id, s.id] = model.NewBoolVar(f"x_{v.id}_{s.id}")

    def var(v_id: str, s_id: str):
        return x.get((v_id, s_id))

    # --- 0) Congelar assignacions ja PUBLICADES (horitzo mobil) ---------------------
    # Si un dia ja s'ha publicat, no el pot tocar el solver -- es fixa com a
    # restriccio dura. Si la parella (vigilant, servei) fixada no te variable
    # (p.ex. dades inconsistents: el vigilant ja no te l'habilitacio), ho
    # avisem en lloc de fallar en silenci.
    avisos: list[str] = []
    if assignacions_fixades:
        for (v_id, s_id), valor in assignacions_fixades.items():
            xv = var(v_id, s_id)
            if xv is None:
                avisos.append(
                    f"assignacio fixada ({v_id}, {s_id}) ignorada: no existeix "
                    f"variable (revisar habilitacio/actiu)"
                )
                continue
            model.Add(xv == valor)

    # --- 1) Cobertura per servei ---------------------------------------------------
    dèficit_vars = []
    for s in serveis:
        candidats = [var(v.id, s.id) for v in vigilants if var(v.id, s.id) is not None]
        if permetre_cobertura_parcial:
            deficit = model.NewIntVar(0, s.vigilants_requerits, f"deficit_{s.id}")
            model.Add(sum(candidats) + deficit == s.vigilants_requerits)
            dèficit_vars.append((s.id, deficit, s.vigilants_requerits))
        else:
            model.Add(sum(candidats) == s.vigilants_requerits)

    # --- 2) Un vigilant no pot cobrir dos serveis que se solapen o que --------------
    #        no respecten el descans minim entre torns
    for v in vigilants:
        if not v.actiu:
            continue
        serveis_v = [s for s in serveis if var(v.id, s.id) is not None]
        for i, s1 in enumerate(serveis_v):
            for s2 in serveis_v[i + 1:]:
                a, b = (s1, s2) if s1.inici <= s2.inici else (s2, s1)
                gap_hores = (b.inici - a.fi).total_seconds() / 3600.0
                requerit = _descans_requerit(a, params)
                if gap_hores < requerit:
                    model.Add(var(v.id, a.id) + var(v.id, b.id) <= 1)

    # --- 3) Jornada maxima setmanal --------------------------------------------------
    setmanes: dict[int, list[Servei]] = {}
    for s in serveis:
        clau = s.inici.isocalendar()[1] * 10000 + s.inici.isocalendar()[0]
        setmanes.setdefault(clau, []).append(s)

    for v in vigilants:
        if not v.actiu:
            continue
        for clau, serveis_setmana in setmanes.items():
            termes = []
            for s in serveis_setmana:
                xv = var(v.id, s.id)
                if xv is not None:
                    # escalem hores x100 per treballar en enters
                    termes.append((xv, int(round(s.durada_hores * 100))))
            if termes:
                model.Add(
                    sum(coef * xv for xv, coef in termes)
                    <= int(round(v.hores_max_setmana * 100))
                )

    # --- 4) Descans setmanal obligatori: FINESTRA MOBIL, no particio fixa per setmana --
    # IMPORTANT: una particio fixa (dilluns-diumenge) pot deixar passar per alt fins a
    # 12-13 dies seguits treballats si el dia de descans cau al principi/final d'una
    # setmana de calendari -- exactament el cas denunciat pels vigilants de Trablisa a
    # la Linia del Valles de FGC (torns de 12 dies seguits). Per evitar-ho, comprovem
    # CADA finestra mobil de N dies consecutius (no nomes els blocs dilluns-diumenge).
    dies_ordenats = sorted({s.inici.date() for s in serveis})
    if dies_ordenats:
        primer_dia, ultim_dia = dies_ordenats[0], dies_ordenats[-1]
        tots_els_dies = [primer_dia + timedelta(days=i) for i in range((ultim_dia - primer_dia).days + 1)]
        n = params.dies_periode_descans_setmanal

        for v in vigilants:
            if not v.actiu:
                continue
            treballa_dia: dict[date, cp_model.IntVar] = {}
            for d in tots_els_dies:
                serveis_dia = [s for s in serveis if s.inici.date() == d and var(v.id, s.id) is not None]
                if not serveis_dia:
                    continue
                tv = model.NewBoolVar(f"treballa_{v.id}_{d}")
                model.AddMaxEquality(tv, [var(v.id, s.id) for s in serveis_dia])
                treballa_dia[d] = tv

            for i in range(len(tots_els_dies) - n + 1):
                finestra = tots_els_dies[i:i + n]
                indicadors = [treballa_dia[d] for d in finestra if d in treballa_dia]
                if indicadors:
                    model.Add(sum(indicadors) <= n - 1)

    # --- 5) Objectiu: equilibri d'hores (prioritari) + preferencies (secundari) -----
    termes_objectiu = []

    for v in vigilants:
        if not v.actiu:
            continue
        hores_assignades = []
        for s in serveis:
            xv = var(v.id, s.id)
            if xv is not None:
                hores_assignades.append((xv, int(round(s.durada_hores * 100))))
        if not hores_assignades:
            continue

        total_var = model.NewIntVar(
            0, int(round(sum(c for _, c in hores_assignades) + v.hores_acumulades * 100)),
            f"hores_{v.id}",
        )
        model.Add(
            total_var
            == sum(coef * xv for xv, coef in hores_assignades) + int(round(v.hores_acumulades * 100))
        )

        objectiu_escalat = int(round((v.hores_objectiu_periode + v.hores_acumulades) * 100))
        desviacio = model.NewIntVar(0, 10_000_000, f"desviacio_{v.id}")
        model.AddAbsEquality(desviacio, total_var - objectiu_escalat)
        termes_objectiu.append((desviacio, pes_equilibri_hores))

        for s in serveis:
            xv = var(v.id, s.id)
            if xv is None:
                continue
            bonus = 0
            if v.zona_preferida and s.zona == v.zona_preferida:
                bonus += 1
            if v.torn_preferit and s.torn == v.torn_preferit:
                bonus += 1
            if bonus:
                # bonus -> restem de la funcio de cost (volem maximitzar-lo)
                termes_objectiu.append((xv, -bonus * pes_preferencia))

    if permetre_cobertura_parcial:
        for s_id, deficit, requerits in dèficit_vars:
            termes_objectiu.append((deficit, 1000))  # penalitzacio molt alta per no cobrir

    model.Minimize(sum(coef * termevar for termevar, coef in termes_objectiu))

    # --- Pistes calentes: seed del solver amb la temptativa anterior ----------------
    # No son restriccions -- nomes indiquen per on començar la cerca. Si una
    # parella ja esta fixada (assignacions_fixades), no cal ni te sentit donar-hi
    # una pista a sobre.
    if pistes_calents:
        for (v_id, s_id), valor in pistes_calents.items():
            if assignacions_fixades and (v_id, s_id) in assignacions_fixades:
                continue
            xv = var(v_id, s_id)
            if xv is not None:
                model.AddHint(xv, valor)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = temps_maxim_segons
    solver.parameters.num_search_workers = 8
    estat = solver.Solve(model)

    estat_text = solver.StatusName(estat)
    assignacions = []
    hores_finals = {v.id: v.hores_acumulades for v in vigilants}
    cobertura_incompleta = []

    if estat in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for (v_id, s_id), xv in x.items():
            if solver.Value(xv) == 1:
                assignacions.append((v_id, s_id))
                s = next(s for s in serveis if s.id == s_id)
                hores_finals[v_id] += s.durada_hores
        if permetre_cobertura_parcial:
            for s_id, deficit, requerits in dèficit_vars:
                coberts = requerits - solver.Value(deficit)
                if coberts < requerits:
                    cobertura_incompleta.append((s_id, coberts, requerits))

    return Resultat(
        assignacions=assignacions,
        hores_finals=hores_finals,
        estat=estat_text,
        cobertura_incompleta=cobertura_incompleta,
        avisos=avisos,
        temps_resolucio_segons=solver.WallTime(),
    )
