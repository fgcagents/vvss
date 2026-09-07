"""
Schemas (models de dades) per al sistema d'assignació de vigilants.

Utilitza Pydantic per validació i documentació automàtica.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Optional


@dataclass
class Vigilant:
    """Model d'un vigilant de seguretat.
    
    Atributs:
        id: Identificador únic del vigilant.
        habilitacions: Conjunt d'habilitacions (ex: {"no_armat", "armat", "cctv"}).
        hores_objectiu_periode: Hores contractuals objectiu per al període planificat.
        hores_acumulades: Hores ja treballades abans d'aquest període.
        hores_max_setmana: Límit màxim d'hores setmanals (default: 48h).
        zona_preferida: Zona preferida per treballar (ex: "Central").
        torn_preferit: Torn preferit (ex: "mati", "tarda", "nit", "24h").
        actiu: Indica si el vigilant està actiu (no de baixa/vacances).
        baixes: Llista d'intervals de baixa (tuples de datetime: inici, fi).
        torns_no_desitjats: Conjunt de torns que el vigilant prefereix evitar.
        binomi_preferit: ID del vigilant amb qui prefereix treballar en binomi (opcional).
    """
    id: str
    habilitacions: set[str]  # p.ex. {"no_armat"}, {"armat", "no_armat"}, {"cctv"}
    hores_objectiu_periode: float  # hores contractuals per al període planificat
    hores_acumulades: float = 0.0  # hores ja fetes abans d'aquest període
    hores_max_setmana: float = 48.0  # topall legal absolut
    zona_preferida: Optional[str] = None
    torn_preferit: Optional[str] = None  # "mati" | "tarda" | "nit" | "24h"
    actiu: bool = True  # False si està de baixa/vacances tot el període
    baixes: list[tuple[datetime, datetime]] = field(default_factory=list)
    torns_no_desitjats: set[str] = field(default_factory=set)
    binomi_preferit: Optional[str] = None  # ID del vigilant amb qui prefereix treballar en binomi


@dataclass
class Servei:
    """Model d'un servei de vigilància.
    
    Atributs:
        id: Identificador únic del servei.
        zona: Zona/estació/linia on es realitza el servei.
        inici: Data i hora d'inici del servei.
        fi: Data i hora de finalització del servei.
        habilitacio_requerida: Habilitació necessària (ex: "armat", "no_armat", "cctv").
        vigilants_requerits: Número mínim de vigilants requerits.
        torn: Etiqueta informativa del torn (ex: "mati", "tarda", "nit", "24h").
        binomi_obligatori: Indica si el servei requereix exactament 2 vigilants (binomi).
    """
    id: str
    zona: str  # estacio, linia o tram
    inici: datetime
    fi: datetime
    habilitacio_requerida: str  # "armat" | "no_armat" | "cctv"
    vigilants_requerits: int = 1
    torn: Optional[str] = None  # etiqueta informativa: "mati"/"tarda"/"nit"/"24h"
    binomi_obligatori: bool = False  # Si True, requereix exactament 2 vigilants

    @property
    def durada_hores(self) -> float:
        """Retorna la durada del servei en hores."""
        return (self.fi - self.inici).total_seconds() / 3600.0


@dataclass
class ParametresLegals:
    """Paràmetres configurables segons conveni o pacte d'empresa.
    
    Atributs:
        descans_minim_hores: Descans mínim general entre jornades (default: 13h).
        descans_minim_auxiliars_hores: Descans mínim per a auxiliars de serveis (default: 12h).
        llindar_torn_llarg_hores: Llindar per considerar un torn com a llarg (default: 20h).
        descans_torn_llarg_hores: Descans mínim després d'un torn llarg (default: 48h).
        dies_periode_descans_setmanal: Període per al descans setmanal (default: 7 dies).
    """
    descans_minim_hores: float = 13.0
    descans_minim_auxiliars_hores: float = 12.0
    # Descans compensatori especial per a torns molt llargs (p.ex. serveis de 24h).
    # Si un servei dura >= llindar_torn_llarg_hores, el descans mínim posterior
    # passa a ser descans_torn_llarg_hores en lloc del descans_minim_hores general.
    llindar_torn_llarg_hores: float = 20.0
    descans_torn_llarg_hores: float = 48.0
    dies_periode_descans_setmanal: int = 7  # cada X dies, com a mínim 1 lliure


@dataclass
class Resultat:
    """Model del resultat de la resolució del solver.
    
    Atributs:
        assignacions: Llista de tuples (vigilant_id, servei_id) assignats.
        hores_finals: Diccionari amb les hores totals per vigilant.
        estat: Estat del solver (ex: "OPTIMAL", "FEASIBLE", "INFEASIBLE").
        cobertura_incompleta: Llista de serveis amb cobertura incompleta.
        avisos: Llista d'avisos generats durant la resolució.
        temps_resolucio_segons: Temps empleat pel solver en segons.
    """
    assignacions: list[tuple[str, str]]  # (vigilant_id, servei_id)
    hores_finals: dict[str, float]
    estat: str
    cobertura_incompleta: list[tuple[str, int, int]]  # (servei_id, coberts, requerits)
    avisos: list[str] = field(default_factory=list)
    temps_resolucio_segons: float = 0.0
