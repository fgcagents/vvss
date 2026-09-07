import csv
from collections import defaultdict

from dades_exemple import genera_serveis, genera_vigilants
from model import ParametresLegals, resol


def main():
    vigilants = genera_vigilants()
    serveis = genera_serveis(dies=7)
    params = ParametresLegals()

    resultat = resol(vigilants, serveis, params)

    print(f"Estat del solver: {resultat.estat}")
    print(f"Serveis totals: {len(serveis)} | Assignacions: {len(resultat.assignacions)}")

    if resultat.cobertura_incompleta:
        print("\n⚠ Serveis amb cobertura incompleta:")
        for s_id, coberts, requerits in resultat.cobertura_incompleta:
            print(f"  - {s_id}: {coberts}/{requerits}")
    else:
        print("\n✓ Tots els serveis coberts.")

    print("\nHores acumulades finals per vigilant:")
    for v in sorted(vigilants, key=lambda v: v.id):
        objectiu = v.hores_objectiu_periode + (v.hores_acumulades)
        final = resultat.hores_finals[v.id]
        print(f"  {v.id}: {final:6.1f}h  (objectiu periode: {v.hores_acumulades + v.hores_objectiu_periode:.1f}h)")

    # Exporta el quadrant a CSV, mateix format que feieu servir a les
    # simulacions de gener amb el motor "per prioritats" de Xivato.
    per_servei = defaultdict(list)
    for v_id, s_id in resultat.assignacions:
        per_servei[s_id].append(v_id)

    with open("quadrant.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["servei_id", "zona", "inici", "fi", "habilitacio", "vigilants_assignats"])
        for s in sorted(serveis, key=lambda s: s.inici):
            writer.writerow([
                s.id, s.zona, s.inici.isoformat(), s.fi.isoformat(),
                s.habilitacio_requerida, ";".join(per_servei.get(s.id, [])),
            ])

    print("\nQuadrant exportat a quadrant.csv")


if __name__ == "__main__":
    main()
