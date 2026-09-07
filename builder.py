"""
Builder: Construcció del model CP-SAT per a l'assignació de vigilants.

Aquest mòdul és responsable de:
1. Crear les variables de decisió (x[vigilant, servei])
2. Afegir totes les restriccions dures (cobertura, descans, habilitacions, etc.)
3. Definir la funció objectiu (equilibri d'hores + preferències)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional

from ortools.sat.python import cp_model

from schemas import Vigilant, Servei, ParametresLegals, Resultat


def _descans_requerit(servei_previ: Servei, params: ParametresLegals) -> float:
    """Calcula el descans mínim requerit després d'un servei."""
    if servei_previ.durada_hores >= params.llindar_torn_llarg_hores:
        return params.descans_torn_llarg_hores
    return params.descans_minim_hores


class ModelBuilder:
    """Builder per al model CP-SAT d'assignació de vigilants.
    
    Atributs:
        model: Model CP-SAT de OR-Tools.
        vigilants: Llista de vigilants.
        serveis: Llista de serveis.
        params: Paràmetres legals.
        x: Diccionari de variables de decisió {(vigilant_id, servei_id): IntVar}.
    """
    
    def __init__(
        self,
        vigilants: list[Vigilant],
        serveis: list[Servei],
        params: ParametresLegals,
    ):
        self.model = cp_model.CpModel()
        self.vigilants = vigilants
        self.serveis = sorted(serveis, key=lambda s: s.inici)
        self.params = params
        self.x: dict[tuple[str, str], cp_model.IntVar] = {}
        self._create_variables()
    
    def _create_variables(self) -> None:
        """Crea les variables de decisió x[vigilant_id, servei_id].
        
        Només crea la variable si:
        1. El vigilant està actiu.
        2. El vigilant té l'habilitació requerida pel servei.
        3. El servei no cau dins d'un període de baixa del vigilant.
        """
        for v in self.vigilants:
            if not v.actiu:
                continue
            for s in self.serveis:
                # Comprovar habilitació
                if s.habilitacio_requerida not in v.habilitacions:
                    continue
                # Comprovar baixes
                en_baixa = False
                for baixa_inici, baixa_fi in v.baixes:
                    if not (s.fi <= baixa_inici or s.inici >= baixa_fi):
                        en_baixa = True
                        break
                if en_baixa:
                    continue
                self.x[v.id, s.id] = self.model.NewBoolVar(f"x_{v.id}_{s.id}")
    
    def var(self, v_id: str, s_id: str) -> Optional[cp_model.IntVar]:
        """Retorna la variable x[v_id, s_id] o None si no existeix."""
        return self.x.get((v_id, s_id))
    
    def add_cobertura_restriccions(self, permetre_cobertura_parcial: bool = True) -> list[tuple]:
        """Afegeix restriccions de cobertura per servei.
        
        Retorna:
            Llista de tuples (servei_id, deficit_var, requerits) si permetre_cobertura_parcial=True.
            Llista buida en cas contrari.
        """
        deficit_vars = []
        for s in self.serveis:
            candidats = [self.var(v.id, s.id) for v in self.vigilants if self.var(v.id, s.id) is not None]
            
            if s.binomi_obligatori:
                # Restricció dura: exactament 2 vigilants per a serveis de binomi
                self.model.Add(sum(candidats) == 2)
            elif permetre_cobertura_parcial:
                deficit = self.model.NewIntVar(0, s.vigilants_requerits, f"deficit_{s.id}")
                self.model.Add(sum(candidats) + deficit == s.vigilants_requerits)
                deficit_vars.append((s.id, deficit, s.vigilants_requerits))
            else:
                self.model.Add(sum(candidats) == s.vigilants_requerits)
        
        return deficit_vars
    
    def add_incompatibilitat_temporal(self) -> None:
        """Afegeix restriccions d'incompatibilitat temporal entre serveis.
        
        Assegura que un vigilant no pot cobrir dos serveis que:
        1. Es solapen temporalment.
        2. No respecten el descans mínim entre ells.
        
        NOTE: Aquesta és la versió O(n²). Per a grans instàncies, considerar
        l'ús de IntervalVar (veure add_incompatibilitat_temporal_optimitzat).
        """
        for v in self.vigilants:
            if not v.actiu:
                continue
            serveis_v = [s for s in self.serveis if self.var(v.id, s.id) is not None]
            for i, s1 in enumerate(serveis_v):
                for s2 in serveis_v[i + 1:]:
                    a, b = (s1, s2) if s1.inici <= s2.inici else (s2, s1)
                    gap_hores = (b.inici - a.fi).total_seconds() / 3600.0
                    requerit = _descans_requerit(a, self.params)
                    if gap_hores < requerit:
                        self.model.Add(self.var(v.id, a.id) + self.var(v.id, b.id) <= 1)
    
    def add_incompatibilitat_temporal_optimitzat(self) -> None:
        """Afegeix restriccions d'incompatibilitat temporal utilitzant IntervalVar.
        
        Aquesta versió és més eficient (O(n log n)) per a grans instàncies.
        """
        for v in self.vigilants:
            if not v.actiu:
                continue
            intervals = []
            for s in self.serveis:
                xv = self.var(v.id, s.id)
                if xv is not None:
                    start = int(s.inici.timestamp())
                    duration = int(s.durada_hores * 3600)
                    interval = self.model.NewOptionalIntervalVar(
                        start, start + duration, xv, f"interval_{v.id}_{s.id}"
                    )
                    intervals.append((s, interval))
            
            # Restricció: Cap solapament entre intervals del mateix vigilant
            if intervals:
                interval_vars = [iv for _, iv in intervals]
                self.model.AddNoOverlap(interval_vars)
            
            # Restricció de descans mínim entre intervals consecutius
            # (Aquesta part és complexa amb IntervalVar, per ara mantenim la versió O(n²))
            # TODO: Implementar amb AddDistance() o restriccions personalitzades
    
    def add_jornada_max_setmanal(self) -> None:
        """Afegeix restricció de jornada màxima setmanal per vigilant."""
        setmanes: dict[int, list[Servei]] = {}
        for s in self.serveis:
            any, setmana, _ = s.inici.isocalendar()
            clau = setmana * 10000 + any
            setmanes.setdefault(clau, []).append(s)

        for v in self.vigilants:
            if not v.actiu:
                continue
            for clau, serveis_setmana in setmanes.items():
                termes = []
                for s in serveis_setmana:
                    xv = self.var(v.id, s.id)
                    if xv is not None:
                        # Escalem hores x100 per treballar en enters
                        termes.append((xv, int(round(s.durada_hores * 100))))
                if termes:
                    self.model.Add(
                        sum(coef * xv for xv, coef in termes)
                        <= int(round(v.hores_max_setmana * 100))
                    )
    
    def add_descans_setmanal(self) -> None:
        """Afegeix restricció de descans setmanal obligatori (finestra mòbil).
        
        Comprova CADA finestra mòbil de N dies consecutius (no només blocs dilluns-diumenge).
        Això evita el problema de torns de 12-13 dies seguits treballats.
        """
        dies_ordenats = sorted({s.inici.date() for s in self.serveis})
        if not dies_ordenats:
            return
        
        primer_dia, ultim_dia = dies_ordenats[0], dies_ordenats[-1]
        tots_els_dies = [primer_dia + timedelta(days=i) for i in range((ultim_dia - primer_dia).days + 1)]
        n = self.params.dies_periode_descans_setmanal

        for v in self.vigilants:
            if not v.actiu:
                continue
            treballa_dia: dict[date, cp_model.IntVar] = {}
            for d in tots_els_dies:
                serveis_dia = [s for s in self.serveis if s.inici.date() == d and self.var(v.id, s.id) is not None]
                if not serveis_dia:
                    continue
                tv = self.model.NewBoolVar(f"treballa_{v.id}_{d}")
                self.model.AddMaxEquality(tv, [self.var(v.id, s.id) for s in serveis_dia])
                treballa_dia[d] = tv

            for i in range(len(tots_els_dies) - n + 1):
                finestra = tots_els_dies[i:i + n]
                indicadors = [treballa_dia[d] for d in finestra if d in treballa_dia]
                if indicadors:
                    self.model.Add(sum(indicadors) <= n - 1)
    
    def add_binomi_preferit(self, pes_preferencia_binomi: int = 5) -> None:
        """Afegeix restriccions toves per a binomis preferits.
        
        Si un vigilant té un binomi_preferit definit, penalitza assignacions
        on treballen separadament.
        """
        # Crear variables per detectar si dos vigilants treballen junts en un servei
        for v1 in self.vigilants:
            if not v1.actiu or not v1.binomi_preferit:
                continue
            v2_id = v1.binomi_preferit
            v2 = next((v for v in self.vigilants if v.id == v2_id), None)
            if not v2 or not v2.actiu:
                continue
            
            for s in self.serveis:
                x1 = self.var(v1.id, s.id)
                x2 = self.var(v2.id, s.id)
                if x1 is not None and x2 is not None:
                    # Penalitzar si treballen separadament en un servei on podrien treballar junts
                    # (Només aplicable si el servei permet més d'un vigilant)
                    if s.vigilants_requerits >= 2:
                        # Crear variable aux per detectar si treballen junts
                        junts = self.model.NewBoolVar(f"binomi_{v1.id}_{v2.id}_{s.id}")
                        self.model.Add(junts == (x1 + x2 == 2))
                        # Penalitzar si NO treballen junts
                        self.model.Add(-pes_preferencia_binomi * junts)
    
    def build_objectiu(
        self,
        pes_equilibri_hores: int = 10,
        pes_preferencia: int = 1,
        pes_equitat_nits: int = 20,
        permetre_cobertura_parcial: bool = True,
        deficit_vars: list[tuple] = None,
    ) -> list[tuple]:
        """Construeix la funció objectiu.
        
        Retorna:
            Llista de tuples (variable, coeficient) per a la funció objectiu.
        """
        termes_objectiu = []
        
        # 1. Equilibri d'hores (prioritari)
        for v in self.vigilants:
            if not v.actiu:
                continue
            hores_assignades = []
            for s in self.serveis:
                xv = self.var(v.id, s.id)
                if xv is not None:
                    hores_assignades.append((xv, int(round(s.durada_hores * 100))))
            if not hores_assignades:
                continue

            total_var = self.model.NewIntVar(
                0, int(round(sum(c for _, c in hores_assignades) + v.hores_acumulades * 100)),
                f"hores_{v.id}",
            )
            self.model.Add(
                total_var
                == sum(coef * xv for xv, coef in hores_assignades) + int(round(v.hores_acumulades * 100))
            )

            objectiu_escalat = int(round((v.hores_objectiu_periode + v.hores_acumulades) * 100))
            desviacio = self.model.NewIntVar(0, 10_000_000, f"desviacio_{v.id}")
            self.model.AddAbsEquality(desviacio, total_var - objectiu_escalat)
            termes_objectiu.append((desviacio, pes_equilibri_hores))

            # 2. Preferències de zona/torn (secundari)
            for s in self.serveis:
                xv = self.var(v.id, s.id)
                if xv is None:
                    continue
                bonus = 0
                if v.zona_preferida and s.zona == v.zona_preferida:
                    bonus += 1
                if v.torn_preferit and s.torn == v.torn_preferit:
                    bonus += 1
                if bonus:
                    termes_objectiu.append((xv, -bonus * pes_preferencia))

        # 3. Equitat en distribució de nits
        nits_per_vigilant: dict[str, cp_model.IntVar] = {}
        for v in self.vigilants:
            if not v.actiu:
                continue
            nits = self.model.NewIntVar(0, len(self.serveis), f"nits_{v.id}")
            nits_vars = [self.var(v.id, s.id) for s in self.serveis 
                        if s.torn == "nit" and self.var(v.id, s.id) is not None]
            if nits_vars:
                self.model.Add(nits == sum(nits_vars))
                nits_per_vigilant[v.id] = nits

        # Calcula mitjana de nits per vigilant actiu
        serveis_nit = [s for s in self.serveis if s.torn == "nit"]
        vigilants_actius = [v for v in self.vigilants if v.actiu]
        if serveis_nit and vigilants_actius:
            mitjana_nits = len(serveis_nit) / len(vigilants_actius)
            for v_id, nits_var in nits_per_vigilant.items():
                desviacio_nits = self.model.NewIntVar(0, 100, f"desv_nits_{v_id}")
                self.model.AddAbsEquality(desviacio_nits, nits_var - int(round(mitjana_nits)))
                termes_objectiu.append((desviacio_nits, pes_equitat_nits))

        # 4. Penalització per torns no desitjats
        for v in self.vigilants:
            if not v.actiu:
                continue
            for s in self.serveis:
                xv = self.var(v.id, s.id)
                if xv is not None and s.torn in v.torns_no_desitjats:
                    termes_objectiu.append((xv, 50))  # Penalització per torn no desitjat

        # 5. Penalització per cobertura incompleta
        if permetre_cobertura_parcial and deficit_vars:
            for s_id, deficit, requerits in deficit_vars:
                termes_objectiu.append((deficit, 1000))  # Penalització molt alta

        return termes_objectiu
    
    def add_hints(self, pistes_calents: dict[tuple[str, str], int] | None = None) -> None:
        """Afegeix pistes calentes (hints) al solver."""
        if pistes_calents:
            for (v_id, s_id), valor in pistes_calents.items():
                xv = self.var(v_id, s_id)
                if xv is not None:
                    self.model.AddHint(xv, valor)
    
    def add_fixades(self, assignacions_fixades: dict[tuple[str, str], int] | None = None) -> list[str]:
        """Afegeix assignacions fixades (restriccions dures).
        
        Retorna:
            Llista d'avisos per assignacions fixades ignorades.
        """
        avisos: list[str] = []
        if assignacions_fixades:
            for (v_id, s_id), valor in assignacions_fixades.items():
                xv = self.var(v_id, s_id)
                if xv is None:
                    avisos.append(
                        f"assignacio fixada ({v_id}, {s_id}) ignorada: no existeix "
                        f"variable (revisar habilitacio/actiu/baixes)"
                    )
                    continue
                self.model.Add(xv == valor)
        return avisos
