"""
Descoberts Manager: Gestió intel·ligent de descoberts en el sistema d'assignació.

Aquest mòdul és responsable de:
1. Detectar automàticament els motius dels descoberts.
2. Registrar els descoberts a la base de dades.
3. Proposar solucions automàtiques.
4. Generar informes i estadístiques.
5. Intentar resoldre els descoberts de manera automàtica.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Tuple
from collections import defaultdict

from schemas import Vigilant, Servei, ParametresLegals, Resultat
from database import (
    obtenir_tots_vigilants, obtenir_tots_serveis, obtenir_parametres_legals,
    obtenir_assignacions_publicades, obtenir_assignacions_actuals,
    registrar_descobert, obtenir_descoberts, obtenir_descoberts_pendents,
    obtenir_descoberts_per_dia, obtenir_motiu_descobert, obtenir_tots_motius_descobert,
    marcar_descobert_com_resolt, obtenir_estadistiques_descoberts,
    obtenir_informe_descoberts_diari, obtenir_dashboard_descoberts
)
from builder import ModelBuilder


def _compatible_temporalment(
    servei1: Servei,
    servei2: Servei,
    params: ParametresLegals,
) -> bool:
    """Comprova si dos serveis son compatibles temporalment per a un mateix vigilant."""
    a, b = (servei1, servei2) if servei1.inici <= servei2.inici else (servei2, servei1)
    
    # 1. Comprovar solapament
    if a.fi > b.inici:
        return False
    
    # 2. Comprovar descans minim
    gap_hores = (b.inici - a.fi).total_seconds() / 3600.0
    requerit = params.descans_torn_llarg_hores if a.durada_hores >= params.llindar_torn_llarg_hores else params.descans_minim_hores
    
    return gap_hores >= requerit


def determinar_motiu_descobert(
    servei: Servei,
    vigilants: List[Vigilant],
    assignacions_actuals: Dict[Tuple[str, str], bool],
    params: ParametresLegals,
    serveis_dict: Optional[Dict[str, Servei]] = None
) -> Dict[str, str]:
    """Determina el motiu d'un descobert de manera intel·ligent.
    
    Args:
        servei: El servei sense cobertura.
        vigilants: Llista de tots els vigilants.
        assignacions_actuals: Assignacions actuals {(vigilant_id, servei_id): publicat}.
        params: Paràmetres legals.
        serveis_dict: Diccionari de serveis per ID (opcional, per optimitzar).
    
    Returns:
        Diccionari amb: cod, descripcio, solucio, categoria, detalls.
    """
    # 1. Filtrar vigilants amb l'habilitació requerida
    candidats = [
        v for v in vigilants
        if v.actiu and servei.habilitacio_requerida in v.habilitacions
    ]
    
    if not candidats:
        return {
            "cod": "falta_habilitacio",
            "descripcio": f"No hi ha vigilants amb l'habilitació {servei.habilitacio_requerida}",
            "solucio": f"Contractar {servei.vigilants_requerits} vigilants amb {servei.habilitacio_requerida}",
            "categoria": "plantilla",
            "detalls": f"Habilitació requerida: {servei.habilitacio_requerida}, Vigilants disponibles: 0"
        }
    
    # 2. Comprovar binomi obligatori
    if servei.binomi_obligatori and len(candidats) < servi.vigilants_requerits:
        return {
            "cod": "binomi_no_disponible",
            "descripcio": f"Només {len(candidats)} vigilants amb habilitació {servei.habilitacio_requerida} (requerits: {servei.vigilants_requerits})",
            "solucio": f"Contractar {servei.vigilants_requerits - len(candidats)} vigilants addicionals amb {servei.habilitacio_requerida}",
            "categoria": "plantilla",
            "detalls": f"Servei {servei.id} requereix {servei.vigilants_requerits} vigilants"
        }
    
    # 3. Filtrar vigilants no en baixa
    candidats_disponibles = []
    for v in candidats:
        en_baixa = False
        for baixa_inici, baixa_fi in v.baixes:
            if not (servei.fi <= baixa_inici or servei.inici >= baixa_fi):
                en_baixa = True
                break
        if not en_baixa:
            candidats_disponibles.append(v)
    
    if not candidats_disponibles:
        return {
            "cod": "tots_en_baixa",
            "descripcio": f"Tots els {len(candidats)} candidats estan de baixa en {servei.inici}",
            "solucio": "Substituir amb vigilants d'altres zones o contractar temporalment",
            "categoria": "temporal",
            "detalls": f"Data servei: {servei.inici.isoformat()}"
        }
    
    # 4. Comprovar conflictes temporals
    conflictes = 0
    for v in candidats_disponibles:
        # Obtenir tots els serveis assignats a aquest vigilant
        serveis_v = []
        for (v_id, s_id) in assignacions_actuals.keys():
            if v_id == v.id:
                serveis_v.append(serveis_dict.get(s_id))
        
        # Comprovar si el servei nou és compatible amb tots els existents
        compatible = True
        for s_existent in serveis_v:
            if s_existent and not _compatible_temporalment(s_existent, servei, params):
                compatible = False
                break
        
        if not compatible:
            conflictes += 1
    
    if conflictes == len(candidats_disponibles):
        return {
            "cod": "sobrecarrega_temporal",
            "descripcio": f"Tots els {len(candidats_disponibles)} candidats tenen conflictes temporals",
            "solucio": "Revisar horaris o augmentar plantilla",
            "categoria": "restriccio",
            "detalls": f"Servei: {servei.id} ({servei.inici} - {servei.fi})"
        }
    
    # 5. Comprovar hores setmanals
    for v in candidats_disponibles:
        # Calcular hores assignades aquesta setmana
        hores_setmana = 0.0
        for (v_id, s_id) in assignacions_actuals.keys():
            if v_id == v.id:
                s = serveis_dict.get(s_id)
                if s:
                    any_s, setmana_s, _ = s.inici.isocalendar()
                    any_servei, setmana_servei, _ = servei.inici.isocalendar()
                    if (any_s, setmana_s) == (any_servei, setmana_servei):
                        hores_setmana += s.durada_hores
        
        if hores_setmana + servei.durada_hores > v.hores_max_setmana:
            return {
                "cod": "hores_setmanals",
                "descripcio": f"Vigilant {v.id} excediria {v.hores_max_setmana}h setmanals ({hores_setmana + servei.durada_hores:.1f}h)",
                "solucio": f"Redistribuir {servei.durada_hores}h a un altre vigilant",
                "categoria": "restriccio",
                "detalls": f"Hores actuals: {hores_setmana:.1f}h, Límit: {v.hores_max_setmana}h"
            }
    
    # 6. Motiu per defecte
    return {
        "cod": "desconegut",
        "descripcio": "No s'ha pogut determinar el motiu automàticament",
        "solucio": "Revisar manualment",
        "categoria": "desconegut",
        "detalls": f"Servei: {servei.id}"
    }


def registrar_descoberts_despres_resolucio(
    resultat: Resultat,
    vigilants: List[Vigilant],
    serveis: List[Servei],
    params: ParametresLegals
) -> List[Dict]:
    """Registra tots els descoberts detectats després d'una resolució.
    
    Args:
        resultat: Resultat del solver.
        vigilants: Llista de vigilants.
        serveis: Llista de serveis.
        params: Paràmetres legals.
    
    Returns:
        Llista de descoberts registrats.
    """
    serveis_dict = {s.id: s for s in serveis}
    assignacions_actuals = obtenir_assignacions_actuals()
    
    descoberts_registrats = []
    
    for s_id, coberts, requerits in resultat.cobertura_incompleta:
        servei = serveis_dict.get(s_id)
        if not servei:
            continue
        
        motiu = determinar_motiu_descobert(
            servei, vigilants, assignacions_actuals, params, serveis_dict
        )
        
        # Registrar el descobert
        descobert_id = registrar_descobert(
            servei_id=s_id,
            data_inici=servei.inici,
            motiu_cod=motiu["cod"],
            detalls=motiu["detalls"],
            solucio_proposada=motiu["solucio"]
        )
        
        # Afegir informació addicional
        motiu_info = obtenir_motiu_descobert(motiu["cod"])
        if motiu_info:
            motiu["prioritat"] = motiu_info["prioritat"]
            motiu["categoria"] = motiu_info["categoria"]
        
        descoberts_registrats.append({
            **motiu,
            "id": descobert_id,
            "servei_id": s_id,
            "data_inici": servei.inici,
            "coberts": coberts,
            "requerits": requerits
        })
    
    return descoberts_registrats


def intentar_resoldre_descobert_automaticament(
    servei_id: str,
    vigilants: List[Vigilant],
    serveis_dict: Dict[str, Servei],
    params: ParametresLegals
) -> Tuple[Optional[str], List[Dict]]:
    """Intenta resoldre un descobert automàticament.
    
    Args:
        servei_id: ID del servei amb descobert.
        vigilants: Llista de vigilants.
        serveis_dict: Diccionari de serveis per ID.
        params: Paràmetres legals.
    
    Returns:
        Tuple amb (vigilant_substitut, candidats_avaluats).
    """
    from urgencia import troba_substitut
    from collections import defaultdict
    
    servei = serveis_dict.get(servei_id)
    if not servei:
        return None, []
    
    # Obtenir assignacions actuals per vigilant
    assignacions_actuals = obtenir_assignacions_actuals()
    serveis_ja_assignats = defaultdict(list)
    for (v_id, s_id) in assignacions_actuals.keys():
        serveis_ja_assignats[v_id].append(serveis_dict.get(s_id))
    
    # Trobar substitut
    vigilant_substitut, candidats = troba_substitut(
        servei, vigilants, serveis_ja_assignats, params
    )
    
    return vigilant_substitut, candidats


def resoldre_descoberts_automaticament(
    limit_prioritat: int = 2
) -> Dict[str, int]:
    """Intenta resoldre automàticament tots els descoberts pendents amb prioritat <= limit_prioritat.
    
    Args:
        limit_prioritat: Només intentar resoldre descoberts amb prioritat <= aquest valor (default: 2).
    
    Returns:
        Diccionari amb estadístiques: {"total": X, "resolts": Y, "fallats": Z}.
    """
    from database import obtenir_servei, obtenir_tots_vigilants, obtenir_parametres_legals
    from integrated_system import SistemaIntegrat
    
    # Obtenir tots els descoberts pendents
    descoberts_pendents = obtenir_descoberts_pendents()
    
    vigilants = obtenir_tots_vigilants()
    serveis_dict = {s.id: s for s in obtenir_tots_serveis()}
    params = obtenir_parametres_legals()
    
    resolts = 0
    fallats = 0
    
    for d in descoberts_pendents:
        # Només processar els de prioritat <= limit_prioritat
        motiu = obtenir_motiu_descobert(d["motiu_cod"])
        prioritat = motiu["prioritat"] if motiu else 4
        if prioritat > limit_prioritat:
            continue
        
        # Intentar resoldre
        vigilant_substitut, candidats = intentar_resoldre_descobert_automaticament(
            d["servei_id"], vigilants, serveis_dict, params
        )
        
        if vigilant_substitut:
            # Marcar com a resolt
            marcar_descobert_com_resolt(d["id"], f"Sistema (auto: {vigilant_substitut})")
            
            # Registrar la substitució a la base de dades
            from database import registrar_substitucio
            registrar_substitucio(
                servei_id=d["servei_id"],
                vigilant_original=None,
                vigilant_substitut=vigilant_substitut,
                motiu=f"Descobert automàtic: {d['motiu_cod']}",
                candidats_avaluats=[
                    {"vigilant_id": c.vigilant_id, "motiu_descart": c.motiu_descart}
                    for c in candidats
                ]
            )
            resolts += 1
        else:
            fallats += 1
    
    return {
        "total": resolts + fallats,
        "resolts": resolts,
        "fallats": fallats
    }


def generar_informe_descoberts(
    data: date = None,
    format: str = "text"
) -> str:
    """Genera un informe de descoberts en diferents formats.
    
    Args:
        data: Data del dia (default: avui).
        format: Format de sortida ("text", "html", "json").
    
    Returns:
        Informe en el format sol·licitat.
    """
    import json
    
    if data is None:
        data = datetime.now().date()
    
    informe = obtenir_informe_descoberts_diari(data)
    
    if format == "json":
        return json.dumps(informe, indent=2, ensure_ascii=False, default=str)
    
    elif format == "html":
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Informe de Descoberts - {data}</title></head>
        <body>
            <h1>Informe de Descoberts - {data}</h1>
            <h2>Resum</h2>
            <p>Serveis totals: {informe['total_serveis']}</p>
            <p>Serveis coberts: {informe['serveis_coberts']} ({informe['percentatge_cobertura']:.1f}%)</p>
            <p>Descoberts totals: {informe['descoberts_total']}</p>
            <p>Descoberts resolts: {informe['descoberts_resolts']}</p>
            <p>Descoberts pendents: {informe['descoberts_pendents']}</p>
            
            <h2>Per Motiu</h2>
            <table border="1">
                <tr><th>Motiu</th><th>Count</th><th>Prioritat</th></tr>
        """
        for motiu, data in informe['per_motiu'].items():
            html += f"<tr><td>{data['descripcio']}</td><td>{data['count']}</td><td>{data['prioritat']}</td></tr>"
        html += "</table>"
        
        if informe['per_zona']:
            html += "<h2>Per Zona</h2><table border='1'><tr><th>Zona</th><th>Count</th></tr>"
            for zona, count in informe['per_zona'].items():
                html += f"<tr><td>{zona}</td><td>{count}</td></tr>"
            html += "</table>"
        
        html += "</body></html>"
        return html
    
    else:  # format == "text"
        lines = []
        lines.append("=" * 80)
        lines.append(f"INFORME DE DESCUBERTS - {data}")
        lines.append("=" * 80)
        lines.append("")
        lines.append("RESUM:")
        lines.append(f"  Serveis totals: {informe['total_serveis']}")
        lines.append(f"  Serveis coberts: {informe['serveis_coberts']} ({informe['percentatge_cobertura']:.1f}%)")
        lines.append(f"  Descoberts totals: {informe['descoberts_total']}")
        lines.append(f"  Descoberts resolts: {informe['descoberts_resolts']}")
        lines.append(f"  Descoberts pendents: {informe['descoberts_pendents']}")
        lines.append("")
        
        if informe['per_motiu']:
            lines.append("PER MOTIU:")
            for motiu, data in informe['per_motiu'].items():
                lines.append(f"  - {data['descripcio']}: {data['count']} (Prioritat: {data['prioritat']})")
            lines.append("")
        
        if informe['per_zona']:
            lines.append("PER ZONA:")
            for zona, count in informe['per_zona'].items():
                lines.append(f"  - {zona}: {count}")
            lines.append("")
        
        if informe['descoberts_detall']:
            lines.append("DETALL:")
            for d in informe['descoberts_detall']:
                status = "✅ RESOLT" if d['resolt'] else "❌ PENDENT"
                lines.append(f"  - {d['servei_id']} ({d['data_inici']}): {d['motiu_descripcio']} {status}")
        
        lines.append("=" * 80)
        return "\n".join(lines)


def enviar_notificacio_descobert(descobert: Dict) -> None:
    """Envia una notificació (consola) quan es detecta un descobert crític.
    
    Args:
        descobert: Diccionari amb les dades del descobert.
    """
    motiu = obtenir_motiu_descobert(descobert["motiu_cod"])
    if motiu and motiu["prioritat"] > 2:
        return
    
    missatge = f"""
    ⚠️  NOU DESCUBERT {motiu['prioritat'] if motiu else 4} ⚠️
    
    Servei: {descobert['servei_id']}
    Data: {descobert['data_inici']}
    Motiu: {motiu['descripcio'] if motiu else 'Desconegut'}
    Categoria: {motiu['categoria'] if motiu else 'desconegut'}
    
    Solució proposada: {descobert.get('solucio_proposada', 'No especificada')}
    Detalls: {descobert.get('detalls', 'No especificats')}
    
    Acció recomanada: {motiu['solucio_tipica'] if motiu else 'Revisar manualment'}
    """
    print(missatge)


def monitoritzar_descoberts() -> None:
    """Monitoritza contínuament els descoberts i intenta resoldre'ls automàticament.
    
    Aquesta funció es pot cridar periòdicament (ex: cada hora) per a:
    1. Detectar nous descoberts.
    2. Intentar resoldre'ls automàticament.
    3. Enviar notificacions per als crítics.
    """
    from database import obtenir_descoberts
    from datetime import datetime, timedelta
    
    avui = datetime.now().date()
    
    # Obtenir descoberts dels últims 2 dies
    data_inici = datetime(avui.year, avui.month, avui.day - 1)
    data_fi = datetime(avui.year, avui.month, avui.day, 23, 59, 59)
    
    descoberts = obtenir_descoberts(
        data_inici=data_inici,
        data_fi=data_fi,
        resolt=False
    )
    
    print(f"\n🔍 Monitoritzant {len(descoberts)} descoberts pendents...")
    
    # Intentar resoldre automàticament
    resultats = resoldre_descoberts_automaticament(limit_prioritat=1)
    print(f"  ✅ Resolts automàticament: {resultats['resolts']}")
    print(f"  ❌ Fallats: {resultats['fallats']}")
    
    # Enviar notificacions per als que no s'han pogut resoldre
    for d in obtenir_descoberts():
        if not d["resolt"]:
            enviar_notificacio_descobert(d)


# ============================================================================
# FUNCIONS D'ALTA NIVELL PER A INTEGRACIÓ
# ============================================================================

def processar_resultat_i_descoberts(
    resultat: Resultat,
    vigilants: List[Vigilant],
    serveis: List[Servei],
    params: ParametresLegals
) -> Dict:
    """Processa el resultat del solver i registra els descoberts.
    
    Args:
        resultat: Resultat del solver.
        vigilants: Llista de vigilants.
        serveis: Llista de serveis.
        params: Paràmetres legals.
    
    Returns:
        Diccionari amb estadístiques dels descoberts registrats.
    """
    # Registrar els descoberts
    descoberts = registrar_descoberts_despres_resolucio(resultat, vigilants, serveis, params)
    
    # Intentar resoldre els crítics automàticament
    serveis_dict = {s.id: s for s in serveis}
    resolts_auto = 0
    for d in descoberts:
        # Obtenir la prioritat del motiu (d té el camp "cod" del motiu)
        motiu_cod = d.get("motiu_cod", d.get("cod", "desconegut"))
        motiu = obtenir_motiu_descobert(motiu_cod)
        prioritat = motiu["prioritat"] if motiu else 4
        
        if prioritat <= 1:  # Només els crítics
            vigilant_substitut, _ = intentar_resoldre_descobert_automaticament(
                d["servei_id"], vigilants, serveis_dict, params
            )
            if vigilant_substitut:
                # Marcar com a resolt
                for dc in obtenir_descoberts(servei_id=d["servei_id"], resolt=False):
                    marcar_descobert_com_resolt(dc["id"], f"Sistema (auto: {vigilant_substitut})")
                resolts_auto += 1
    
    return {
        "descoberts_totals": len(descoberts),
        "descoberts_resolts_automaticament": resolts_auto,
        "descoberts_pendents": len(descoberts) - resolts_auto,
        "detall": descoberts
    }
