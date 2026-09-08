"""
Sistema Integrat: Rolling Horizon + Substitucions d'Urgència amb Base de Dades.

Aquest mòdul integra:
1. Rolling Horizon per a planificació contínua amb equitat.
2. Substitucions d'urgència per a descoberts immediats.
3. Persistència amb SQLite per a mantenir l'estat entre execucions.

Flux de treball:
- El sistema executa Rolling Horizon per a planificar els pròxims dies.
- Quan hi ha un descobert (baixa, malaltia, etc.), s'activa el mode urgència.
- Les substitucions d'urgència s'integren amb l'estat de Rolling Horizon.
- Tot es guarda a la base de dades SQLite.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Tuple
from collections import defaultdict

from schemas import Vigilant, Servei, ParametresLegals, Resultat
from solver import resol, valida_resultat
from exporter import exporta_a_csv, exporta_a_json, imprimeix_quadrant, genera_estadistiques
from database import (
    obtenir_tots_vigilants, obtenir_tots_serveis, obtenir_parametres_legals,
    obtenir_assignacions_publicades, obtenir_assignacions_temptatives,
    guardar_assignacions, publicar_assignacions, registrar_substitucio,
    guardar_estat_rolling_horizon, obtenir_estat_rolling_horizon, importar_dades_exemple,
    obtenir_hores_acumulades, DB_PATH, obtenir_servei,
    obtenir_assignacions_actuals,
)


@dataclass
class SistemaIntegrat:
    """Sistema integrat de planificació amb Rolling Horizon i substitucions d'urgència.
    
    Atributs:
        dies_finestra: Nombre de dies de la finestra de planificació.
        dies_lookback: Nombre de dies de lookback per a restriccions de descans.
        dies_horitzo_total: Nombre total de dies a planificar.
    """
    dies_finestra: int = 5
    dies_lookback: int = 2
    dies_horitzo_total: int = 14
    
    def __init__(
        self,
        dies_finestra: int = 5,
        dies_lookback: int = 2,
        dies_horitzo_total: int = 14,
    ):
        self.dies_finestra = dies_finestra
        self.dies_lookback = dies_lookback
        self.dies_horitzo_total = dies_horitzo_total
    
    def _dia_index(self, s: Servei) -> int:
        """Extreu l'índex del dia des del servei ID (format: ZONA-TORN-DIA)."""
        try:
            return int(s.id.rsplit("-", 1)[1])
        except (ValueError, IndexError):
            # Si el format no és el esperat, calcular des de la data
            inici_periode = datetime(2026, 9, 7, 0, 0)
            return (s.inici.date() - inici_periode.date()).days
    
    def _amb_hores_actualitzades(
        self, 
        vigilants: List[Vigilant], 
        hores_publicades: Dict[str, float]
    ) -> List[Vigilant]:
        """Actualitza les hores acumulades dels vigilants."""
        actualitzats = []
        for v in vigilants:
            hores = hores_publicades.get(v.id, v.hores_acumulades)
            nou = Vigilant(**{**v.__dict__, "hores_acumulades": hores})
            actualitzats.append(nou)
        return actualitzats
    
    def _obtenir_serveis_finestra(
        self, 
        tots_els_serveis: Dict[str, Servei],
        dia_inici: int,
        dia_fi: int
    ) -> List[Servei]:
        """Obté els serveis dins d'una finestra de dies."""
        return [
            s for s in tots_els_serveis.values()
            if dia_inici <= self._dia_index(s) < dia_fi
        ]
    

    def _compatible_temporalment(
        self,
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

    def _troba_substitut(
        self,
        servei_urgent: Servei,
        vigilants: List[Vigilant],
        serveis_ja_assignats: Dict[str, List[Servei]],
        params: ParametresLegals
    ) -> Tuple[Optional[str], List[Dict]]:
        """Troba un substitut per a un servei d'urgència.
        
        Returns:
            Tuple amb (vigilant_substitut_id, candidats_avaluats).
        """
        from dataclasses import dataclass as dc
        
        @dc
        class Candidat:
            vigilant_id: str
            hores_acumulades: float
            motiu_descart: Optional[str] = None
        
        candidats = []
        
        # 1. Filtrar vigilants amb l'habilitació requerida
        for v in vigilants:
            if v.actiu and servei_urgent.habilitacio_requerida in v.habilitacions:
                candidats.append(Candidat(
                    vigilant_id=v.id,
                    hores_acumulades=v.hores_acumulades
                ))
        
        # 2. Filtrar vigilants no en baixa
        candidats_disponibles = []
        for c in candidats:
            v = next(vig for vig in vigilants if vig.id == c.vigilant_id)
            en_baixa = any(
                not (servei_urgent.fi <= baixa_inici or servei_urgent.inici >= baixa_fi)
                for baixa_inici, baixa_fi in v.baixes
            )
            if not en_baixa:
                candidats_disponibles.append(c)
        
        # 3. Comprovar compatibilitat temporal amb serveis ja assignats
        for c in candidats_disponibles:
            v = next(vig for vig in vigilants if vig.id == c.vigilant_id)
            serveis_vigilant = serveis_ja_assignats.get(v.id, [])
            
            for s_assignat in serveis_vigilant:
                if not self._compatible_temporalment(s_assignat, servei_urgent, params):
                    c.motiu_descart = f"Conflicte temporal amb {s_assignat.id}"
                    break
            else:
                # 4. Comprovar hores setmanals
                hores_servei = servei_urgent.durada_hores
                hores_totals = c.hores_acumulades + hores_servei
                if hores_totals > v.hores_max_setmana:
                    c.motiu_descart = f"Excedeix hores setmanals ({hores_totals:.1f}/{v.hores_max_setmana})"
        
        # 5. Ordenar candidats per hores acumulades (preferir els menys carregats)
        candidats_valids = [c for c in candidats_disponibles if c.motiu_descart is None]
        candidats_valids.sort(key=lambda c: c.hores_acumulades)
        
        if candidats_valids:
            return candidats_valids[0].vigilant_id, [{"vigilant_id": c.vigilant_id, "hores_acumulades": c.hores_acumulades, "motiu_descart": c.motiu_descart} for c in candidats]
        else:
            return None, candidats
    def inicialitzar_sistema(self) -> None:
        """Inicialitza el sistema amb dades d'exemple."""
        importar_dades_exemple()
        print(f"✅ Sistema inicialitzat amb dades d'exemple ({DB_PATH})")
    
    def executar_rolling_horizon(self) -> None:
        """Executa el procés de Rolling Horizon complet.
        
        Flux:
        1. Carrega vigilants, serveis i paràmetres de la BD.
        2. Per cada finestra de dies:
           a. Resol amb pistes calentes de l'anterior.
           b. Publica el primer dia de la finestra.
           c. Guarda l'estat.
        """
        vigilants = obtenir_tots_vigilants()
        tots_els_serveis = {s.id: s for s in obtenir_tots_serveis()}
        params = obtenir_parametres_legals()
        
        # Carregar estat anterior si existeix
        estat_anterior = obtenir_estat_rolling_horizon()
        
        # Inicialitzar hores publicades
        hores_publicades = {v.id: obtenir_hores_acumulades(v.id) for v in vigilants}
        
        # Inicialitzar assignacions publicades
        publicat: Dict[Tuple[str, str], bool] = obtenir_assignacions_publicades()
        
        # Inicialitzar pistes calentes
        tentatiu_anterior: Dict[Tuple[str, str], int] = obtenir_assignacions_temptatives()
        
        print(f"\n{'='*80}")
        print("INICIANT ROLLING HORIZON")
        print(f"{'='*80}")
        print(f"Finestra: {self.dies_finestra} dies | Lookback: {self.dies_lookback} dies")
        print(f"Horitzó total: {self.dies_horitzo_total} dies")
        print(f"Vigilants: {len(vigilants)} | Serveis: {len(tots_els_serveis)}")
        print(f"{'='*80}\n")
        
        for dia_publicar in range(self.dies_horitzo_total - self.dies_finestra + 1):
            dia_lookback_inici = max(0, dia_publicar - self.dies_lookback)
            serveis_finestra = self._obtenir_serveis_finestra(
                tots_els_serveis, 
                dia_lookback_inici, 
                dia_publicar + self.dies_finestra
            )
            
            # Assignacions fixades: look-back + dies ja publicats dins la finestra
            fixades = {
                (v_id, s_id): 1
                for (v_id, s_id), valor in publicat.items()
                if s_id in {s.id for s in serveis_finestra}
            }
            
            vigilants_actualitzats = self._amb_hores_actualitzades(vigilants, hores_publicades)
            
            # Resoldre amb pistes calentes
            resultat = resol(
                vigilants_actualitzats, 
                serveis_finestra, 
                params,
                assignacions_fixades=fixades,
                pistes_calents=tentatiu_anterior,
                temps_maxim_segons=10.0,
            )
            
            # Validar resultat
            errors = valida_resultat(
                resultat,
                vigilants_actualitzats,
                serveis_finestra,
                params,
                permetre_cobertura_parcial=True,
            )
            
            # Publiquem només el primer dia de la finestra (dia_publicar)
            serveis_avui = [s for s in serveis_finestra if self._dia_index(s) == dia_publicar]
            ids_avui = {s.id for s in serveis_avui}
            assignats_avui = [(v, s) for v, s in resultat.assignacions if s in ids_avui]
            
            # Guardar assignacions a la BD
            guardar_assignacions(resultat.assignacions, publicat=False)
            
            # Publicar les assignacions d'avui
            for v_id, s_id in assignats_avui:
                publicat[(v_id, s_id)] = True
                hores_publicades[v_id] = hores_publicades.get(v_id, 0.0) + tots_els_serveis[s_id].durada_hores
            
            # Publicar a la BD
            publicar_assignacions(list(ids_avui))
            
            # Actualitzar pistes calentes per a la propera iteració
            tentatiu_anterior = {
                (v, s): 1 for v, s in resultat.assignacions if s not in ids_avui
            }
            
            # Guardar estat de Rolling Horizon
            guardar_estat_rolling_horizon(
                data_inici=serveis_finestra[0].inici if serveis_finestra else datetime.now(),
                data_fi=serveis_finestra[-1].fi if serveis_finestra else datetime.now(),
                finestra_actual=dia_publicar,
                dies_publicats=dia_publicar + 1,
                temps_resolucio_segons=resultat.temps_resolucio_segons,
                estat_solver=resultat.estat,
            )
            
            # Processar descoberts i registrar-los
            from descoberts_manager import processar_resultat_i_descoberts
            stats_descoberts = processar_resultat_i_descoberts(
                resultat, 
                vigilants_actualitzats, 
                serveis_finestra, 
                params
            )
            
            # Mostrar progress
            print(
                f"Dia {dia_publicar:>2} | "
                f"Estat: {resultat.estat:<9} | "
                f"Temps: {resultat.temps_resolucio_segons:>6.3f}s | "
                f"Assignats avui: {len(assignats_avui)} | "
                f"Cobertura incompleta: {len(resultat.cobertura_incompleta)} | "
                f"Descoberts: {stats_descoberts['descoberts_totals']} (Resolts: {stats_descoberts['descoberts_resolts_automaticament']})"
            )
            
            if errors:
                print(f"  ⚠️  Errors de validació: {len(errors)}")
                for error in errors[:3]:  # Mostrar només els primers 3
                    print(f"     - {error}")
        
        # Mostrar resultat final
        print(f"\n{'='*80}")
        print("RESULTAT FINAL DE ROLLING HORIZON")
        print(f"{'='*80}")
        
        # Carregar totes les assignacions publicades
        assignacions_finals = obtenir_assignacions_publicades()
        serveis_publicats = [s for s in tots_els_serveis.values() if any(s.id == s_id for (_, s_id) in assignacions_finals.keys())]
        
        print(f"Total assignacions publicades: {len(assignacions_finals)}")
        print(f"Hores finals per vigilant:")
        for v in sorted(vigilants, key=lambda v: v.id):
            print(f"  {v.id}: {hores_publicades.get(v.id, 0):.1f}h")
        
        # Guardar estadístiques
        stats = genera_estadistiques(
            Resultat(
                assignacions=list(assignacions_finals.keys()),
                hores_finals=hores_publicades,
                estat="COMPLET",
                cobertura_incompleta=[],
            ),
            vigilants,
            serveis_publicats,
        )
        print(f"\nEstadístiques: {stats['general']}")
    
    def gestionar_substitucio_urgent(
        self,
        servei_id: str,
        motiu: str = "malaltia"
    ) -> Tuple[Optional[str], List[Dict]]:
        """Gestiona una substitució d'urgència per a un servei.
        
        Args:
            servei_id: ID del servei que necessita substitució.
            motiu: Motiu de la substitució (ex: "malaltia", "baixa", "vacances").
        
        Returns:
            Tuple amb (vigilant_substitut, candidats_avaluats).
        """
        # Substitució d'urgència integrada directament
        
        # Carregar dades de la BD
        vigilants = obtenir_tots_vigilants()
        serveis = obtenir_tots_serveis()
        params = obtenir_parametres_legals()
        
        servei_urgent = obtenir_servei(servei_id)
        if not servei_urgent:
            print(f"❌ Servei {servei_id} no trobat.")
            return None, []
        
        # Obtenir assignacions actuals per a cada vigilant
        assignacions_actuals = obtenir_assignacions_actuals()
        serveis_ja_assignats = defaultdict(list)
        for (v_id, s_id), publicat in assignacions_actuals.items():
            serveis_ja_assignats[v_id].append(obtenir_servei(s_id))
        
        # Trobar substitut (utilitzem la funció local)
        vigilant_substitut, candidats = self._troba_substitut(
            servei_urgent, 
            vigilants, 
            serveis_ja_assignats, 
            params
        )
        
        if vigilant_substitut:
            # Obtenir el vigilant original (si n'hi havia)
            vigilant_original = None
            for (v_id, s_id), publicat in assignacions_actuals.items():
                if s_id == servei_id:
                    vigilant_original = v_id
                    break
            
            # Registrar substitució a la BD
            registrar_substitucio(
                servei_id=servei_id,
                vigilant_original=vigilant_original,
                vigilant_substitut=vigilant_substitut,
                motiu=motiu,
                candidats_avaluats=[
                    {"vigilant_id": c.vigilant_id, "hores_acumulades": c.hores_acumulades, "motiu_descart": c.motiu_descart}
                    for c in candidats
                ]
            )
            
            print(f"✅ Substitució registrada: {vigilant_substitut} -> {servei_id} ({motiu})")
        else:
            print(f"❌ No s'ha trobat substitut per a {servei_id}")
        
        return vigilant_substitut, [
            {"vigilant_id": c.vigilant_id, "hores_acumulades": c.hores_acumulades, "motiu_descart": c.motiu_descart}
            for c in candidats
        ]
    
    def obtenir_quadrant_actual(self) -> Resultat:
        """Obté el quadrant actual des de la base de dades."""
        vigilants = obtenir_tots_vigilants()
        serveis = obtenir_tots_serveis()
        assignacions = obtenir_assignacions_publicades()
        
        # Calcular hores finals
        hores_finals = {v.id: obtenir_hores_acumulades(v.id) for v in vigilants}
        
        return Resultat(
            assignacions=[(v_id, s_id) for (v_id, s_id) in assignacions.keys()],
            hores_finals=hores_finals,
            estat="PUBLICAT",
            cobertura_incompleta=[],
            avisos=[],
            temps_resolucio_segons=0.0,
        )
    
    def exportar_quadrant_actual(self, format: str = "csv") -> None:
        """Exporta el quadrant actual a CSV o JSON."""
        resultat = self.obtenir_quadrant_actual()
        vigilants = obtenir_tots_vigilants()
        serveis = obtenir_tots_serveis()
        
        if format == "csv":
            exporta_a_csv(resultat, vigilants, serveis, "quadrant_actual.csv")
            print(f"✅ Quadrant exportat a quadrant_actual.csv")
        elif format == "json":
            exporta_a_json(resultat, vigilants, serveis, "quadrant_actual.json")
            print(f"✅ Quadrant exportat a quadrant_actual.json")
        else:
            imprimeix_quadrant(resultat, vigilants, serveis)


# ============================================================================
# FUNCIONS D'ALTA NIVELL PER A ÚS DIRECTE
# ============================================================================

def executar_sistema_complet() -> None:
    """Executa el sistema complet: inicialització + Rolling Horizon."""
    sistema = SistemaIntegrat(
        dies_finestra=5,
        dies_lookback=2,
        dies_horitzo_total=14,
    )
    
    # Inicialitzar amb dades d'exemple
    sistema.inicialitzar_sistema()
    
    # Executar Rolling Horizon
    sistema.executar_rolling_horizon()
    
    # Exportar resultat
    sistema.exportar_quadrant_actual("csv")
    sistema.exportar_quadrant_actual("json")


def gestionar_urgencia(servei_id: str, motiu: str = "malaltia") -> None:
    """Gestiona una urgència de manera independent."""
    sistema = SistemaIntegrat()
    vigilant_substitut, candidats = sistema.gestionar_substitucio_urgent(servei_id, motiu)
    
    if vigilant_substitut:
        print(f"\n✅ Substitució realitzada:")
        print(f"   Servei: {servei_id}")
        print(f"   Substitut: {vigilant_substitut}")
        print(f"   Motiu: {motiu}")
        print(f"\n   Candidats avaluats:")
        for c in candidats[:5]:  # Mostrar només els primers 5
            estat = "✅ VALID" if c["motiu_descart"] is None else f"❌ {c['motiu_descart']}"
            print(f"     {c['vigilant_id']}: {c['hores_acumulades']:.1f}h - {estat}")


# ============================================================================
# DEMO: PROVA DEL SISTEMA INTEGRAT
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "urgencia":
        # Mode urgència: gestionar una substitució
        if len(sys.argv) > 2:
            servei_id = sys.argv[2]
            motiu = sys.argv[3] if len(sys.argv) > 3 else "malaltia"
            gestionar_urgencia(servei_id, motiu)
        else:
            print("Ús: python integrated_system.py urgencia <servei_id> [motiu]")
            print("Exemple: python integrated_system.py urgencia CEN-nit-0 malaltia")
    else:
        # Mode complet: executar sistema sencer
        executar_sistema_complet()
