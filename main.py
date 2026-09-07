import csv
from collections import defaultdict

from dades_exemple import genera_serveis, genera_vigilants
from schemas import ParametresLegals
from solver import resol, valida_resultat
from exporter import exporta_a_csv, imprimeix_quadrant


def main():
    vigilants = genera_vigilants()
    serveis = genera_serveis(dies=7)
    params = ParametresLegals()

    print("🔍 Resolent problema d'assignació de vigilants...")
    print(f"   Vigilants: {len([v for v in vigilants if v.actiu])} actius / {len(vigilants)} totals")
    print(f"   Serveis: {len(serveis)}")
    print(f"   Binomis obligatoris: {sum(1 for s in serveis if s.binomi_obligatori)}")
    
    # Resoldre amb les noves opcions
    resultat = resol(
        vigilants, 
        serveis, 
        params,
        pes_equilibri_hores=10,
        pes_preferencia=1,
        pes_equitat_nits=20,
        permetre_cobertura_parcial=True,
        temps_maxim_segons=30.0,
    )

    # Validar el resultat
    errors = valida_resultat(resultat, vigilants, serveis, params)
    
    # Imprimir quadrant
    imprimeix_quadrant(resultat, vigilants, serveis)
    
    # Exportar a CSV
    exporta_a_csv(resultat, vigilants, serveis, "quadrant.csv")
    print("\n✅ Quadrant exportat a quadrant.csv")
    
    # Mostrar errors de validació (si n'hi ha)
    if errors:
        print("\n❌ ERRORS DE VALIDACIÓ:")
        for error in errors:
            print(f"   - {error}")
    else:
        print("\n✅ Resultat vàlid: totes les restriccions legals es compleixen.")

    # Mostrar avisos del solver
    if resultat.avisos:
        print("\n⚠️  Avisos del solver:")
        for avis in resultat.avisos:
            print(f"   - {avis}")


if __name__ == "__main__":
    main()
