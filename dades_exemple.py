"""
Generador de dades d'exemple: una xarxa ferroviaria petita amb 3 estacions,
torns de mati/tarda/nit + un lloc amb servei de 24h, i una plantilla mixta
de vigilants armats/no armats/CCTV.

Aquesta versió inclou:
- Binomis obligatoris per a torns de nit (segons Pla de Seguretat de FGC)
- Baixes puntuals per a vigilants
- Torns no desitjats
- Preferències de binomi

Nomes serveix per provar el motor. Substituiu-ho per les vostres
dades reals quan connecteu això amb el sistema de producció.
"""

from datetime import datetime, timedelta

from schemas import Vigilant, Servei


def genera_vigilants() -> list[Vigilant]:
    # Serveis sense armes de foc: només categories "no_armat" (control d'accessos,
    # rondes, atenció a usuaris) i "cctv" (sala de control/videovigilància).
    # Afegim més vigilants amb CCTV per cobrir els torns de nit amb binomi.
    # També afegim baixes i preferències de binomi per a proves.
    return [
        # Vigilants amb CCTV per a torns de nit
        Vigilant(
            "V01", {"no_armat", "cctv"}, 
            hores_objectiu_periode=80, 
            hores_acumulades=310, 
            zona_preferida="Central", 
            torn_preferit="nit",
            torns_no_desitjats={"mati"},
            binomi_preferit="V02",  # Prefereix treballar amb V02
        ),
        Vigilant(
            "V02", {"no_armat", "cctv"}, 
            hores_objectiu_periode=80, 
            hores_acumulades=295, 
            zona_preferida="Central", 
            torn_preferit="nit",
            binomi_preferit="V01",  # Prefereix treballar amb V01
        ),
        Vigilant(
            "V03", {"no_armat", "cctv"}, 
            hores_objectiu_periode=80, 
            hores_acumulades=340, 
            zona_preferida="Nord", 
            torn_preferit="nit",
            torns_no_desitjats={"mati"},
        ),
        Vigilant(
            "V04", {"no_armat", "cctv"}, 
            hores_objectiu_periode=80, 
            hores_acumulades=260, 
            zona_preferida="Nord", 
            torn_preferit="nit",
            binomi_preferit="V03",
        ),
        # Vigilants sense CCTV per a torns de dia
        Vigilant(
            "V05", {"no_armat"}, 
            hores_objectiu_periode=80, 
            hores_acumulades=280, 
            zona_preferida="Central", 
            torn_preferit="mati",
            torns_no_desitjats={"nit"},
        ),
        Vigilant(
            "V06", {"no_armat"}, 
            hores_objectiu_periode=80, 
            hores_acumulades=300, 
            zona_preferida="Central", 
            torn_preferit="tarda",
            torns_no_desitjats={"nit"},
        ),
        Vigilant(
            "V07", {"no_armat"}, 
            hores_objectiu_periode=80, 
            hores_acumulades=275, 
            zona_preferida="Sud", 
            torn_preferit="mati",
        ),
        Vigilant(
            "V08", {"no_armat"}, 
            hores_objectiu_periode=80, 
            hores_acumulades=290, 
            zona_preferida="Sud", 
            torn_preferit="tarda",
        ),
        # Vigilants amb baixa per a proves
        Vigilant(
            "V09", {"no_armat", "cctv"}, 
            hores_objectiu_periode=80, 
            hores_acumulades=320, 
            zona_preferida="Nord", 
            torn_preferit="nit",
            # Baixa del dia 2 al dia 4
            baixes=[(
                datetime(2026, 9, 8, 0, 0),
                datetime(2026, 9, 10, 23, 59)
            )],
        ),
        Vigilant(
            "V10", {"no_armat"}, 
            hores_objectiu_periode=40, 
            hores_acumulades=150, 
            zona_preferida="Central", 
            torn_preferit="mati",
        ),  # part-time
    ]


def genera_serveis(dies: int = 7) -> list[Servei]:
    serveis: list[Servei] = []
    inici_periode = datetime(2026, 9, 7, 0, 0)  # dilluns

    torns = [
        ("mati", 6, 14),
        ("tarda", 14, 22),
        ("nit", 22, 30),  # travessa mitjanit -> 30 = 6h del dia seguent
    ]

    def requerits_per_torn(torn: str) -> int:
        # Pla de Seguretat de FGC (avalat pels Mossos d'Esquadra): els vigilants
        # han de treballar en PARELLA de 22h a 6h; la resta de franges, en unitat.
        # Vegeu estudi_legal_fgc.md, secció 2.
        return 1

    for d in range(dies):
        dia = inici_periode + timedelta(days=d)

        # Estació Central: control d'accessos (no armat) mati+tarda, CCTV nit
        for torn, h_ini, h_fi in torns:
            hab = "cctv" if torn == "nit" else "no_armat"
            # Els torns de nit a Central requereixen binomi obligatori
            binomi = (torn == "nit")
            serveis.append(Servei(
                id=f"CEN-{torn}-{d}",
                zona="Central",
                inici=dia + timedelta(hours=h_ini),
                fi=dia + timedelta(hours=h_fi),
                habilitacio_requerida=hab,
                vigilants_requerits=2 if binomi else 1,
                torn=torn,
                binomi_obligatori=binomi,
            ))

        # Estació Nord: rondes no armades, 3 torns
        for torn, h_ini, h_fi in torns:
            # Els torns de nit a Nord sempre requereixen binomi
            binomi = (torn == "nit")
            serveis.append(Servei(
                id=f"NOR-{torn}-{d}",
                zona="Nord",
                inici=dia + timedelta(hours=h_ini),
                fi=dia + timedelta(hours=h_fi),
                habilitacio_requerida="no_armat",
                vigilants_requerits=2 if binomi else 1,
                torn=torn,
                binomi_obligatori=binomi,
            ))

        # Estació Sud: control d'accessos no armat, només mati+tarda (sense servei de nit)
        for torn, h_ini, h_fi in torns[:2]:
            serveis.append(Servei(
                id=f"SUD-{torn}-{d}",
                zona="Sud",
                inici=dia + timedelta(hours=h_ini),
                fi=dia + timedelta(hours=h_fi),
                habilitacio_requerida="no_armat",
                vigilants_requerits=1,
                torn=torn,
                binomi_obligatori=False,
            ))

    return serveis


def genera_xarxa_realista(
    num_estacions: int = 5,
    dies: int = 7,
    vigilants_per_estacio: int = 4,
    percentatge_cctv: float = 0.3,
    percentatge_binomi_nit: float = 0.8,
) -> tuple[list[Vigilant], list[Servei]]:
    """Genera una xarxa ferroviària realista per a proves d'escalabilitat.
    
    Args:
        num_estacions: Número d'estacions (default: 5).
        dies: Número de dies a planificar (default: 7).
        vigilants_per_estacio: Vigilants per estació (default: 4).
        percentatge_cctv: Percentatge de vigilants amb habilitació CCTV (default: 0.3).
        percentatge_binomi_nit: Percentatge de torns de nit que requereixen binomi (default: 0.8).
    
    Returns:
        Tuple amb (vigilants, serveis).
    """
    import random
    random.seed(42)  # Per a resultats reproducibles
    
    # Generar estacions
    estacions = [f"Estacio_{i:02d}" for i in range(num_estacions)]
    
    # Generar vigilants
    vigilants = []
    vigilant_id = 1
    for _ in range(num_estacions * vigilants_per_estacio):
        habilitacions = {"no_armat"}
        if random.random() < percentatge_cctv:
            habilitacions.add("cctv")
        
        # Assignar zona preferida aleatòriament
        zona_preferida = random.choice(estacions) if estacions else None
        
        # Torn preferit aleatori
        torn_preferit = random.choice(["mati", "tarda", "nit", None])
        
        # Torns no desitjats (aleatori)
        torns_no_desitjats = set()
        if random.random() < 0.5:
            torns_no_desitjats.add(random.choice(["mati", "tarda", "nit"]))
        
        vigilants.append(Vigilant(
            f"V{vigilant_id:03d}",
            habilitacions=habilitacions,
            hores_objectiu_periode=80 + random.randint(-10, 10),
            hores_acumulades=random.randint(250, 350),
            zona_preferida=zona_preferida,
            torn_preferit=torn_preferit,
            torns_no_desitjats=torns_no_desitjats,
        ))
        vigilant_id += 1
    
    # Generar serveis
    serveis = []
    inici_periode = datetime(2026, 9, 7, 0, 0)
    torns = [
        ("mati", 6, 14),
        ("tarda", 14, 22),
        ("nit", 22, 30),
    ]
    
    for d in range(dies):
        dia = inici_periode + timedelta(days=d)
        for estacio in estacions:
            for torn, h_ini, h_fi in torns:
                # Determinar habilitació requerida
                if torn == "nit":
                    hab = "cctv" if random.random() < 0.5 else "no_armat"
                else:
                    hab = "no_armat"
                
                # Determinar si és binomi obligatori (només per nit)
                binomi = (torn == "nit" and random.random() < percentatge_binomi_nit)
                
                serveis.append(Servei(
                    id=f"{estacio}-{torn}-{d}",
                    zona=estacio,
                    inici=dia + timedelta(hours=h_ini),
                    fi=dia + timedelta(hours=h_fi),
                    habilitacio_requerida=hab,
                    vigilants_requerits=2 if binomi else 1,
                    torn=torn,
                    binomi_obligatori=binomi,
                ))
    
    return vigilants, serveis
