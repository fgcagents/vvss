"""
Solver: Execució del solver CP-SAT i extracció de resultats.

Aquest mòdul és responsable de:
1. Configurar i executar el solver CP-SAT.
2. Extreure el resultat i validar-lo.
3. Retornar el resultat en format estructurat.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from ortools.sat.python import cp_model

from schemas import Vigilant, Servei, ParametresLegals, Resultat
from builder import ModelBuilder


def resol(
    vigilants: list[Vigilant],
    serveis: list[Servei],
    params: ParametresLegals,
    pes_equilibri_hores: int = 10,
    pes_preferencia: int = 1,
    pes_equitat_nits: int = 20,
    permetre_cobertura_parcial: bool = True,
    temps_maxim_segons: float = 30.0,
    assignacions_fixades: dict[tuple[str, str], int] | None = None,
    pistes_calents: dict[tuple[str, str], int] | None = None,
    usar_interval_var: bool = False,
) -> Resultat:
    """Resol el problema d'assignació de vigilants utilitzant CP-SAT.
    
    Args:
        vigilants: Llista de vigilants disponibles.
        serveis: Llista de serveis a cobrir.
        params: Paràmetres legals per a restriccions.
        pes_equilibri_hores: Pes per a l'equilibri d'hores (default: 10).
        pes_preferencia: Pes per a preferències de zona/torn (default: 1).
        pes_equitat_nits: Pes per a equitat en distribució de nits (default: 20).
        permetre_cobertura_parcial: Si True, permet cobertura incompleta (default: True).
        temps_maxim_segons: Temps màxim d'execució en segons (default: 30).
        assignacions_fixades: Assignacions ja publicades (restricció dura).
        pistes_calents: Assignacions temptatives de l'última resolució (hints).
        usar_interval_var: Si True, utilitza IntervalVar per a restriccions temporals (default: False).
    
    Returns:
        Resultat: Objecte amb les assignacions, hores finals, estat, etc.
    """
    builder = ModelBuilder(vigilants, serveis, params)
    
    # 1. Afegir restriccions de cobertura
    deficit_vars = builder.add_cobertura_restriccions(permetre_cobertura_parcial)
    
    # 2. Afegir restriccions d'incompatibilitat temporal
    if usar_interval_var:
        builder.add_incompatibilitat_temporal_optimitzat()
    else:
        builder.add_incompatibilitat_temporal()
    
    # 3. Afegir restricció de jornada màxima setmanal
    builder.add_jornada_max_setmanal()
    
    # 4. Afegir restricció de descans setmanal (finestra mòbil)
    builder.add_descans_setmanal()
    
    # 5. Afegir assignacions fixades (restriccions dures)
    avisos = builder.add_fixades(assignacions_fixades)
    
    # 6. Afegir pistes calentes (hints)
    builder.add_hints(pistes_calents)
    
    # 7. Construir funció objectiu
    termes_objectiu = builder.build_objectiu(
        pes_equilibri_hores=pes_equilibri_hores,
        pes_preferencia=pes_preferencia,
        pes_equitat_nits=pes_equitat_nits,
        permetre_cobertura_parcial=permetre_cobertura_parcial,
        deficit_vars=deficit_vars,
    )
    
    # 8. Minimitzar la funció objectiu
    builder.model.Minimize(sum(coef * termevar for termevar, coef in termes_objectiu))
    
    # 9. Configurar i executar el solver
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = temps_maxim_segons
    solver.parameters.num_search_workers = 8
    solver.parameters.log_search_progress = False
    
    estat = solver.Solve(builder.model)
    estat_text = solver.StatusName(estat)
    
    # 10. Extreure el resultat
    assignacions = []
    hores_finals = {v.id: v.hores_acumulades for v in vigilants}
    cobertura_incompleta = []
    
    if estat in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for (v_id, s_id), xv in builder.x.items():
            if solver.Value(xv) == 1:
                assignacions.append((v_id, s_id))
                s = next(s for s in serveis if s.id == s_id)
                hores_finals[v_id] += s.durada_hores
        
        if permetre_cobertura_parcial:
            for s_id, deficit, requerits in deficit_vars:
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


def valida_resultat(
    resultat: Resultat,
    vigilants: list[Vigilant],
    serveis: list[Servei],
    params: ParametresLegals,
) -> list[str]:
    """Valida que el resultat compleix totes les restriccions legals.
    
    Args:
        resultat: Resultat del solver a validar.
        vigilants: Llista de vigilants.
        serveis: Llista de serveis.
        params: Paràmetres legals.
    
    Returns:
        Llista d'errors trobats (buida si tot és correcte).
    """
    errors = []
    assignacions_dict = {(v, s): True for v, s in resultat.assignacions}
    serveis_dict = {s.id: s for s in serveis}
    vigilants_dict = {v.id: v for v in vigilants}
    
    # 1. Validar cobertura mínima
    for s in serveis:
        coberts = sum(1 for v in vigilants if assignacions_dict.get((v.id, s.id)))
        if s.binomi_obligatori:
            if coberts != 2:
                errors.append(f"Servei {s.id} (binomi obligatori): {coberts} vigilants (requerits: 2)")
        elif coberts < s.vigilants_requerits:
            errors.append(f"Servei {s.id}: només {coberts}/{s.vigilants_requerits} vigilants")
    
    # 2. Validar descans mínim entre serveis
    for v in vigilants:
        serveis_v = [s for s in serveis if assignacions_dict.get((v.id, s.id))]
        serveis_v_sorted = sorted(serveis_v, key=lambda s: s.inici)
        for i in range(len(serveis_v_sorted) - 1):
            gap = (serveis_v_sorted[i+1].inici - serveis_v_sorted[i].fi).total_seconds() / 3600
            requerit = params.descans_torn_llarg_hores if serveis_v_sorted[i].durada_hores >= params.llindar_torn_llarg_hores else params.descans_minim_hores
            if gap < requerit:
                errors.append(
                    f"Vigilant {v.id}: descans de {gap:.1f}h entre {serveis_v_sorted[i].id} i {serveis_v_sorted[i+1].id} "
                    f"(requerit: {requerit}h)"
                )
    
    # 3. Validar jornada màxima setmanal
    for v in vigilants:
        serveis_v = [s for s in serveis if assignacions_dict.get((v.id, s.id))]
        hores_setmana = {}
        for s in serveis_v:
            any, setmana, _ = s.inici.isocalendar()
            clau = (any, setmana)
            hores_setmana[clau] = hores_setmana.get(clau, 0) + s.durada_hores
        for (any, setmana), hores in hores_setmana.items():
            if hores > v.hores_max_setmana:
                errors.append(
                    f"Vigilant {v.id}: {hores:.1f}h a la setmana {setmana} (màxim: {v.hores_max_setmana}h)"
                )
    
    # 4. Validar descans setmanal (finestra mòbil)
    for v in vigilants:
        serveis_v = [s for s in serveis if assignacions_dict.get((v.id, s.id))]
        dies_treballats = {s.inici.date() for s in serveis_v}
        if not dies_treballats:
            continue
        
        primer_dia = min(dies_treballats)
        ultim_dia = max(dies_treballats)
        tots_els_dies = [primer_dia + timedelta(days=i) for i in range((ultim_dia - primer_dia).days + 1)]
        n = params.dies_periode_descans_setmanal
        
        for i in range(len(tots_els_dies) - n + 1):
            finestra = tots_els_dies[i:i + n]
            dies_treballats_finestra = [d for d in finestra if d in dies_treballats]
            if len(dies_treballats_finestra) == n:
                errors.append(
                    f"Vigilant {v.id}: sense dia lliure en {finestra[0]} a {finestra[-1]}"
                )
    
    # 5. Validar assignacions a vigilants inactius
    for v_id, s_id in resultat.assignacions:
        v = vigilants_dict.get(v_id)
        if v and not v.actiu:
            errors.append(f"Assignació a vigilant inactiu: {v_id} -> {s_id}")
    
    # 6. Validar assignacions a vigilants en baixa
    for v_id, s_id in resultat.assignacions:
        v = vigilants_dict.get(v_id)
        s = serveis_dict.get(s_id)
        if v and s:
            for baixa_inici, baixa_fi in v.baixes:
                if not (s.fi <= baixa_inici or s.inici >= baixa_fi):
                    errors.append(f"Assignació a vigilant en baixa: {v_id} -> {s_id} (baixa: {baixa_inici} a {baixa_fi})")
    
    # 7. Validar habilitacions
    for v_id, s_id in resultat.assignacions:
        v = vigilants_dict.get(v_id)
        s = serveis_dict.get(s_id)
        if v and s and s.habilitacio_requerida not in v.habilitacions:
            errors.append(f"Assignació sense habilitació: {v_id} (habilitacions: {v.habilitacions}) -> {s_id} (requerida: {s.habilitacio_requerida})")
    
    return errors
