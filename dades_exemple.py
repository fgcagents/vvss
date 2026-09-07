"""
Generador de dades d'exemple: una xarxa ferroviaria petita amb 3 estacions,
torns de mati/tarda/nit + un lloc amb servei de 24h, i una plantilla mixta
de vigilants armats/no armats/CCTV.

Nomes serveix per provar el motor (model.py). Substituiu-ho per les vostres
dades reals (planificacio de serveis contractats + plantilla real amb TIP
i categories) quan connecteu aixo amb Xivato.
"""

from datetime import datetime, timedelta

from model import Vigilant, Servei


def genera_vigilants() -> list[Vigilant]:
    # Serveis sense armes de foc: nomes categories "no_armat" (control d'accessos,
    # rondes, atencio a usuaris) i "cctv" (sala de control/videovigilancia).
    return [
        Vigilant("V01", {"no_armat"}, hores_objectiu_periode=80, hores_acumulades=310, zona_preferida="Central", torn_preferit="mati"),
        Vigilant("V02", {"no_armat"}, hores_objectiu_periode=80, hores_acumulades=295, zona_preferida="Central", torn_preferit="tarda"),
        Vigilant("V03", {"no_armat", "cctv"}, hores_objectiu_periode=80, hores_acumulades=340, zona_preferida="Nord", torn_preferit="nit"),
        Vigilant("V04", {"no_armat"}, hores_objectiu_periode=80, hores_acumulades=260, zona_preferida="Sud", torn_preferit="mati"),
        Vigilant("V05", {"no_armat"}, hores_objectiu_periode=80, hores_acumulades=330, zona_preferida="Nord", torn_preferit="tarda"),
        Vigilant("V06", {"cctv", "no_armat"}, hores_objectiu_periode=80, hores_acumulades=300, zona_preferida="Central", torn_preferit="nit"),
        Vigilant("V07", {"no_armat"}, hores_objectiu_periode=80, hores_acumulades=275, zona_preferida="Sud", torn_preferit="tarda"),
        Vigilant("V08", {"no_armat"}, hores_objectiu_periode=40, hores_acumulades=150, zona_preferida="Central", torn_preferit="mati"),  # part-time
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
        # Vegeu estudi_legal_fgc.md, seccio 2.
        return 2 if torn == "nit" else 1

    for d in range(dies):
        dia = inici_periode + timedelta(days=d)

        # Estacio Central: control d'accessos (no armat) mati+tarda, CCTV nit
        for torn, h_ini, h_fi in torns:
            hab = "cctv" if torn == "nit" else "no_armat"
            serveis.append(Servei(
                id=f"CEN-{torn}-{d}",
                zona="Central",
                inici=dia + timedelta(hours=h_ini),
                fi=dia + timedelta(hours=h_fi),
                habilitacio_requerida=hab,
                vigilants_requerits=requerits_per_torn(torn),
                torn=torn,
            ))

        # Estacio Nord: rondes no armades, 3 torns
        for torn, h_ini, h_fi in torns:
            serveis.append(Servei(
                id=f"NOR-{torn}-{d}",
                zona="Nord",
                inici=dia + timedelta(hours=h_ini),
                fi=dia + timedelta(hours=h_fi),
                habilitacio_requerida="no_armat",
                vigilants_requerits=requerits_per_torn(torn),
                torn=torn,
            ))

        # Estacio Sud: control d'accessos no armat, nomes mati+tarda (sense servei de nit)
        for torn, h_ini, h_fi in torns[:2]:
            serveis.append(Servei(
                id=f"SUD-{torn}-{d}",
                zona="Sud",
                inici=dia + timedelta(hours=h_ini),
                fi=dia + timedelta(hours=h_fi),
                habilitacio_requerida="no_armat",
                vigilants_requerits=1,
                torn=torn,
            ))

    return serveis
