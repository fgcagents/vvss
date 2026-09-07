"""
Exporter: Exportació de resultats a diferents formats.

Aquest mòdul és responsable de:
1. Exportar el quadrat a CSV (format compatible amb Xivato).
2. Exportar el resultat a JSON per a integració amb altres sistemes.
3. Generar informació estadística del resultat.
"""

import csv
import json
from collections import defaultdict
from datetime import datetime
from typing import Optional

from schemas import Vigilant, Servei, Resultat


def exporta_a_csv(
    resultat: Resultat,
    vigilants: list[Vigilant],
    serveis: list[Servei],
    path: str = "quadrant.csv",
) -> None:
    """Exporta el resultat a un fitxer CSV.
    
    Args:
        resultat: Resultat del solver.
        vigilants: Llista de vigilants.
        serveis: Llista de serveis.
        path: Camí del fitxer CSV (default: "quadrant.csv").
    """
    per_servei = defaultdict(list)
    for v_id, s_id in resultat.assignacions:
        per_servei[s_id].append(v_id)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["servei_id", "zona", "inici", "fi", "habilitacio", "torn", "vigilants_assignats", "binomi_obligatori"])
        for s in sorted(serveis, key=lambda s: s.inici):
            writer.writerow([
                s.id,
                s.zona,
                s.inici.isoformat(),
                s.fi.isoformat(),
                s.habilitacio_requerida,
                s.torn or "",
                ";".join(per_servei.get(s.id, [])),
                s.binomi_obligatori,
            ])


def exporta_a_json(
    resultat: Resultat,
    vigilants: list[Vigilant],
    serveis: list[Servei],
    params: Optional[dict] = None,
    path: str = "quadrant.json",
) -> None:
    """Exporta el resultat a un fitxer JSON.
    
    Args:
        resultat: Resultat del solver.
        vigilants: Llista de vigilants.
        serveis: Llista de serveis.
        params: Paràmetres utilitzats (opcional).
        path: Camí del fitxer JSON (default: "quadrant.json").
    """
    # Preparar dades per a JSON
    vigilants_dict = {v.id: {
        "id": v.id,
        "habilitacions": list(v.habilitacions),
        "hores_objectiu_periode": v.hores_objectiu_periode,
        "hores_acumulades": v.hores_acumulades,
        "hores_max_setmana": v.hores_max_setmana,
        "zona_preferida": v.zona_preferida,
        "torn_preferit": v.torn_preferit,
        "actiu": v.actiu,
        "hores_finals": resultat.hores_finals.get(v.id, v.hores_acumulades),
    } for v in vigilants}
    
    serveis_dict = {s.id: {
        "id": s.id,
        "zona": s.zona,
        "inici": s.inici.isoformat(),
        "fi": s.fi.isoformat(),
        "habilitacio_requerida": s.habilitacio_requerida,
        "vigilants_requerits": s.vigilants_requerits,
        "torn": s.torn,
        "binomi_obligatori": s.binomi_obligatori,
        "durada_hores": s.durada_hores,
    } for s in serveis}
    
    # Assignacions per vigilant
    assignacions_per_vigilant = defaultdict(list)
    for v_id, s_id in resultat.assignacions:
        assignacions_per_vigilant[v_id].append(s_id)
    
    # Assignacions per servei
    assignacions_per_servei = defaultdict(list)
    for v_id, s_id in resultat.assignacions:
        assignacions_per_servei[s_id].append(v_id)
    
    # Estadístiques
    estadistiques = {
        "total_serveis": len(serveis),
        "serveis_coberts": len(serveis) - len(resultat.cobertura_incompleta),
        "serveis_sense_cobertura": len(resultat.cobertura_incompleta),
        "total_assignacions": len(resultat.assignacions),
        "vigilants_actius": sum(1 for v in vigilants if v.actiu),
        "temps_resolucio_segons": resultat.temps_resolucio_segons,
        "estat_solver": resultat.estat,
    }
    
    # Cobertura incompleta
    cobertura_incompleta = [
        {"servei_id": s_id, "coberts": coberts, "requerits": requerits}
        for s_id, coberts, requerits in resultat.cobertura_incompleta
    ]
    
    # Resultat final
    resultat_json = {
        "metadata": {
            "data_generacio": datetime.now().isoformat(),
            "estat": resultat.estat,
            "temps_resolucio_segons": resultat.temps_resolucio_segons,
            "params": params or {},
        },
        "estadistiques": estadistiques,
        "vigilants": vigilants_dict,
        "serveis": serveis_dict,
        "assignacions": {
            "per_vigilant": {v_id: s_ids for v_id, s_ids in assignacions_per_vigilant.items()},
            "per_servei": {s_id: v_ids for s_id, v_ids in assignacions_per_servei.items()},
        },
        "cobertura_incompleta": cobertura_incompleta,
        "avisos": resultat.avisos,
    }
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(resultat_json, f, indent=2, ensure_ascii=False)


def genera_estadistiques(
    resultat: Resultat,
    vigilants: list[Vigilant],
    serveis: list[Servei],
) -> dict:
    """Genera estadístiques del resultat.
    
    Args:
        resultat: Resultat del solver.
        vigilants: Llista de vigilants.
        serveis: Llista de serveis.
    
    Returns:
        Diccionari amb estadístiques.
    """
    # Assignacions per vigilant
    assignacions_per_vigilant = defaultdict(list)
    for v_id, s_id in resultat.assignacions:
        assignacions_per_vigilant[v_id].append(s_id)
    
    # Assignacions per servei
    assignacions_per_servei = defaultdict(list)
    for v_id, s_id in resultat.assignacions:
        assignacions_per_servei[s_id].append(v_id)
    
    # Hores per vigilant
    hores_per_vigilant = {v.id: resultat.hores_finals.get(v.id, v.hores_acumulades) for v in vigilants}
    
    # Distribució de torns
    torns_per_vigilant = defaultdict(lambda: defaultdict(int))
    serveis_dict = {s.id: s for s in serveis}
    for v_id, s_id in resultat.assignacions:
        s = serveis_dict.get(s_id)
        if s and s.torn:
            torns_per_vigilant[v_id][s.torn] += 1
    
    # Distribució per zona
    zones_per_vigilant = defaultdict(lambda: defaultdict(int))
    for v_id, s_id in resultat.assignacions:
        s = serveis_dict.get(s_id)
        if s:
            zones_per_vigilant[v_id][s.zona] += 1
    
    # Serveis per zona
    serveis_per_zona = defaultdict(int)
    for s in serveis:
        serveis_per_zona[s.zona] += 1
    
    # Serveis coberts per zona
    serveis_coberts_per_zona = defaultdict(int)
    for s in serveis:
        if s.id in assignacions_per_servei:
            serveis_coberts_per_zona[s.zona] += 1
    
    return {
        "general": {
            "total_serveis": len(serveis),
            "serveis_coberts": len(serveis) - len(resultat.cobertura_incompleta),
            "serveis_sense_cobertura": len(resultat.cobertura_incompleta),
            "percentatge_cobertura": (1 - len(resultat.cobertura_incompleta) / len(serveis)) * 100 if serveis else 100,
            "total_assignacions": len(resultat.assignacions),
            "vigilants_actius": sum(1 for v in vigilants if v.actiu),
            "vigilants_assignats": len(assignacions_per_vigilant),
        },
        "hores": {
            "per_vigilant": hores_per_vigilant,
            "mitjana_hores": sum(hores_per_vigilant.values()) / len(hores_per_vigilant) if hores_per_vigilant else 0,
            "max_hores": max(hores_per_vigilant.values()) if hores_per_vigilant else 0,
            "min_hores": min(hores_per_vigilant.values()) if hores_per_vigilant else 0,
        },
        "torns": {
            "per_vigilant": dict(torns_per_vigilant),
            "distribucio_global": defaultdict(int),
        },
        "zones": {
            "serveis_per_zona": dict(serveis_per_zona),
            "serveis_coberts_per_zona": dict(serveis_coberts_per_zona),
            "cobertura_per_zona": {
                zona: (serveis_coberts_per_zona[zona] / serveis_per_zona[zona] * 100) if serveis_per_zona[zona] > 0 else 0
                for zona in serveis_per_zona
            },
        },
        "cobertura_incompleta": [
            {"servei_id": s_id, "coberts": coberts, "requerits": requerits, "percentatge": (coberts / requerits * 100) if requerits > 0 else 0}
            for s_id, coberts, requerits in resultat.cobertura_incompleta
        ],
    }


def imprimeix_quadrant(
    resultat: Resultat,
    vigilants: list[Vigilant],
    serveis: list[Servei],
) -> None:
    """Imprimeix el quadrant per consola en format llegible.
    
    Args:
        resultat: Resultat del solver.
        vigilants: Llista de vigilants.
        serveis: Llista de serveis.
    """
    serveis_dict = {s.id: s for s in serveis}
    vigilants_dict = {v.id: v for v in vigilants}
    
    # Ordenar serveis per data i hora
    serveis_ordenats = sorted(serveis, key=lambda s: s.inici)
    
    print("\n" + "=" * 80)
    print("QUADRANT D'ASSIGNACIONS")
    print("=" * 80)
    print(f"Estat: {resultat.estat} | Temps: {resultat.temps_resolucio_segons:.3f}s")
    print(f"Assignacions: {len(resultat.assignacions)} | Cobertura incompleta: {len(resultat.cobertura_incompleta)}")
    print("-" * 80)
    
    # Agrupar per dia
    assignacions_per_dia = defaultdict(list)
    for v_id, s_id in resultat.assignacions:
        s = serveis_dict[s_id]
        dia = s.inici.date()
        assignacions_per_dia[dia].append((v_id, s_id, s))
    
    for dia in sorted(assignacions_per_dia.keys()):
        print(f"\n📅 {dia.strftime('%A, %Y-%m-%d')}")
        print("-" * 40)
        
        # Agrupar per zona
        assignacions_per_zona = defaultdict(list)
        for v_id, s_id, s in assignacions_per_dia[dia]:
            assignacions_per_zona[s.zona].append((v_id, s_id, s))
        
        for zona in sorted(assignacions_per_zona.keys()):
            print(f"  📍 {zona}:")
            for v_id, s_id, s in sorted(assignacions_per_zona[zona], key=lambda x: x[2].inici):
                v = vigilants_dict[v_id]
                print(f"    {s.inici.strftime('%H:%M')} - {s.fi.strftime('%H:%M')}: {v_id} ({s.torn or 'N/A'}, {s.habilitacio_requerida}) {'[BINOMI]' if s.binomi_obligatori else ''}")
    
    # Cobertura incompleta
    if resultat.cobertura_incompleta:
        print("\n⚠️  COBERTURA INCOMPLETA:")
        for s_id, coberts, requerits in resultat.cobertura_incompleta:
            s = serveis_dict[s_id]
            print(f"  🚨 {s_id} ({s.zona}, {s.inici.strftime('%Y-%m-%d %H:%M')}): {coberts}/{requerits} vigilants")
    
    # Hores finals per vigilant
    print("\n📊 HORES FINALES PER VIGILANT:")
    print("-" * 40)
    for v in sorted(vigilants, key=lambda v: v.id):
        objectiu = v.hores_objectiu_periode + v.hores_acumulades
        final = resultat.hores_finals.get(v.id, v.hores_acumulades)
        desviacio = final - objectiu
        print(f"  {v.id}: {final:6.1f}h (objectiu: {objectiu:.1f}h, {'+' if desviacio >= 0 else ''}{desviacio:+.1f}h)")
    
    print("\n" + "=" * 80)


def exporta_a_dataframe(
    resultat: Resultat,
    vigilants: list[Vigilant],
    serveis: list[Servei],
):
    """Exporta el resultat a un DataFrame de pandas.
    
    Args:
        resultat: Resultat del solver.
        vigilants: Llista de vigilants.
        serveis: Llista de serveis.
    
    Returns:
        DataFrame amb el quadrant.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("Pandas no està instal·lat. Executa: pip install pandas")
    
    # Preparar dades
    data = []
    serveis_dict = {s.id: s for s in serveis}
    vigilants_dict = {v.id: v for v in vigilants}
    
    for v_id, s_id in resultat.assignacions:
        s = serveis_dict[s_id]
        v = vigilants_dict[v_id]
        data.append({
            "vigilant_id": v_id,
            "servei_id": s_id,
            "zona": s.zona,
            "inici": s.inici,
            "fi": s.fi,
            "torn": s.torn or "N/A",
            "habilitacio": s.habilitacio_requerida,
            "durada_hores": s.durada_hores,
            "binomi_obligatori": s.binomi_obligatori,
            "zona_preferida": v.zona_preferida,
            "torn_preferit": v.torn_preferit,
        })
    
    return pd.DataFrame(data)
