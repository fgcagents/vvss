"""
Database: Gestió de la base de dades SQLite per al sistema d'assignació de vigilants.

Aquest mòdul és responsable de:
1. Crear i inicialitzar la base de dades SQLite.
2. Gestionar totes les operacions CRUD per a vigilants, serveis, assignacions, etc.
3. Proporcionar funcions per a carregar/desar l'estat del sistema.
"""

import sqlite3
from datetime import datetime, date, time
from typing import Optional, List, Dict, Tuple
from pathlib import Path

from schemas import Vigilant, Servei, ParametresLegals, Resultat


# Configuració de la base de dades
DB_PATH = Path("vvss.db")


def _connect() -> sqlite3.Connection:
    """Retorna una connexió a la base de dades."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Inicialitza la base de dades amb totes les taules necessàries."""
    with _connect() as conn:
        cursor = conn.cursor()
        
        # Taula: vigilants
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vigilants (
                id TEXT PRIMARY KEY,
                habilitacions TEXT NOT NULL,  -- JSON array: ["no_armat", "cctv"]
                hores_objectiu_periode REAL NOT NULL,
                hores_acumulades REAL DEFAULT 0.0,
                hores_max_setmana REAL DEFAULT 48.0,
                zona_preferida TEXT,
                torn_preferit TEXT,
                actiu BOOLEAN DEFAULT 1,
                torns_no_desitjats TEXT,  -- JSON array: ["nit", "mati"]
                binomi_preferit TEXT,
                data_creacio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_actualitzacio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Taula: serveis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS serveis (
                id TEXT PRIMARY KEY,
                zona TEXT NOT NULL,
                inici TIMESTAMP NOT NULL,
                fi TIMESTAMP NOT NULL,
                habilitacio_requerida TEXT NOT NULL,
                vigilants_requerits INTEGER DEFAULT 1,
                torn TEXT,
                binomi_obligatori BOOLEAN DEFAULT 0,
                data_creacio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Taula: assignacions (estat actual)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assignacions (
                vigilant_id TEXT NOT NULL,
                servei_id TEXT NOT NULL,
                data_assignacio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                publicat BOOLEAN DEFAULT 0,  -- Si s'ha publicat (no es pot modificar)
                PRIMARY KEY (vigilant_id, servei_id),
                FOREIGN KEY (vigilant_id) REFERENCES vigilants(id),
                FOREIGN KEY (servei_id) REFERENCES serveis(id)
            )
        """)
        
        # Taula: baixes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS baixes (
                vigilant_id TEXT NOT NULL,
                inici TIMESTAMP NOT NULL,
                fi TIMESTAMP NOT NULL,
                motiu TEXT,
                data_creacio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (vigilant_id, inici, fi),
                FOREIGN KEY (vigilant_id) REFERENCES vigilants(id)
            )
        """)
        
        # Taula: historic_assignacions (registre de totes les assignacions històriques)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historic_assignacions (
                vigilant_id TEXT NOT NULL,
                servei_id TEXT NOT NULL,
                data_assignacio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_desassignacio TIMESTAMP,
                motiu TEXT,  -- Ex: "substitució", "replanificació", "publicació"
                FOREIGN KEY (vigilant_id) REFERENCES vigilants(id),
                FOREIGN KEY (servei_id) REFERENCES serveis(id)
            )
        """)
        
        # Taula: historic_substitucions (registre de substitucions d'urgència)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historic_substitucions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                servei_id TEXT NOT NULL,
                vigilant_original TEXT,
                vigilant_substitut TEXT NOT NULL,
                data_substitucio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                motiu TEXT NOT NULL,  -- Ex: "baixa", "malaltia", "vacances"
                candidats_avaluats TEXT,  -- JSON: [{"vigilant_id": "V01", "motiu": "..."}]
                FOREIGN KEY (servei_id) REFERENCES serveis(id),
                FOREIGN KEY (vigilant_original) REFERENCES vigilants(id),
                FOREIGN KEY (vigilant_substitut) REFERENCES vigilants(id)
            )
        """)
        
        # Taula: parametres_legals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parametres_legals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descans_minim_hores REAL NOT NULL,
                descans_minim_auxiliars_hores REAL NOT NULL,
                llindar_torn_llarg_hores REAL NOT NULL,
                descans_torn_llarg_hores REAL NOT NULL,
                dies_periode_descans_setmanal INTEGER NOT NULL,
                data_actualitzacio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                actiu BOOLEAN DEFAULT 1
            )
        """)
        
        # Taula: rolling_horizon_estat (estat actual de l'horitzó mòbil)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rolling_horizon_estat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_inici TIMESTAMP NOT NULL,
                data_fi TIMESTAMP NOT NULL,
                finestra_actual INTEGER NOT NULL,  -- Dies des de data_inici
                dies_publicats INTEGER NOT NULL,  -- Dies ja publicats
                data_ultima_resolucio TIMESTAMP,
                temps_resolucio_segons REAL,
                estat_solver TEXT
            )
        """)
        
        # Taula: estadistiques (registre d'estadístiques històriques)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS estadistiques (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_serveis INTEGER,
                serveis_coberts INTEGER,
                serveis_sense_cobertura INTEGER,
                vigilants_actius INTEGER,
                vigilants_assignats INTEGER,
                mitjana_hores REAL,
                max_hores REAL,
                min_hores REAL
            )
        """)
        
        # Inserir paràmetres legals per defecte si no existeixen
        cursor.execute("SELECT COUNT(*) FROM parametres_legals WHERE actiu = 1")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO parametres_legals 
                (descans_minim_hores, descans_minim_auxiliars_hores, 
                 llindar_torn_llarg_hores, descans_torn_llarg_hores, 
                 dies_periode_descans_setmanal, actiu)
                VALUES (13.0, 12.0, 20.0, 48.0, 7, 1)
            """)
        
        conn.commit()


def reset_db() -> None:
    """Esborra totes les taules i reinicialitza la base de dades."""
    # No s'elimina el fitxer: a Windows pot estar obert per una altra
    # connexió del procés i unlink() falla encara que la BD sigui vàlida.
    init_db()
    with _connect() as conn:
        for table in (
            "assignacions",
            "historic_assignacions",
            "historic_substitucions",
            "baixes",
            "serveis",
            "vigilants",
            "rolling_horizon_estat",
            "estadistiques",
            "parametres_legals",
        ):
            conn.execute(f"DELETE FROM {table}")
        conn.commit()
    init_db()


# ============================================================================
# FUNCIONS DE CONVERSIÓ ENTRE SQL I OBJECTES
# ============================================================================

def _row_to_vigilant(row: sqlite3.Row) -> Vigilant:
    """Converteix una fila de la BD a un objecte Vigilant."""
    import json
    
    habilitacions = set(json.loads(row["habilitacions"])) if row["habilitacions"] else set()
    torns_no_desitjats = set(json.loads(row["torns_no_desitjats"])) if row["torns_no_desitjats"] else set()
    
    # Carregar baixes des de la taula baixes
    baixes = []
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT inici, fi FROM baixes WHERE vigilant_id = ?",
            (row["id"],)
        )
        for baixa_row in cursor.fetchall():
            baixes.append((
                datetime.fromisoformat(baixa_row["inici"]),
                datetime.fromisoformat(baixa_row["fi"])
            ))
    
    return Vigilant(
        id=row["id"],
        habilitacions=habilitacions,
        hores_objectiu_periode=row["hores_objectiu_periode"],
        hores_acumulades=row["hores_acumulades"],
        hores_max_setmana=row["hores_max_setmana"],
        zona_preferida=row["zona_preferida"],
        torn_preferit=row["torn_preferit"],
        actiu=bool(row["actiu"]),
        baixes=baixes,
        torns_no_desitjats=torns_no_desitjats,
        binomi_preferit=row["binomi_preferit"],
    )


def _vigilant_to_row(v: Vigilant) -> Dict:
    """Converteix un objecte Vigilant a un diccionari per a la BD."""
    import json
    
    return {
        "id": v.id,
        "habilitacions": json.dumps(list(v.habilitacions)),
        "hores_objectiu_periode": v.hores_objectiu_periode,
        "hores_acumulades": v.hores_acumulades,
        "hores_max_setmana": v.hores_max_setmana,
        "zona_preferida": v.zona_preferida,
        "torn_preferit": v.torn_preferit,
        "actiu": int(v.actiu),
        "torns_no_desitjats": json.dumps(list(v.torns_no_desitjats)),
        "binomi_preferit": v.binomi_preferit,
    }


def _row_to_servei(row: sqlite3.Row) -> Servei:
    """Converteix una fila de la BD a un objecte Servei."""
    return Servei(
        id=row["id"],
        zona=row["zona"],
        inici=datetime.fromisoformat(row["inici"]),
        fi=datetime.fromisoformat(row["fi"]),
        habilitacio_requerida=row["habilitacio_requerida"],
        vigilants_requerits=row["vigilants_requerits"],
        torn=row["torn"],
        binomi_obligatori=bool(row["binomi_obligatori"]),
    )


def _servei_to_row(s: Servei) -> Dict:
    """Converteix un objecte Servei a un diccionari per a la BD."""
    return {
        "id": s.id,
        "zona": s.zona,
        "inici": s.inici.isoformat(),
        "fi": s.fi.isoformat(),
        "habilitacio_requerida": s.habilitacio_requerida,
        "vigilants_requerits": s.vigilants_requerits,
        "torn": s.torn,
        "binomi_obligatori": int(s.binomi_obligatori),
    }


def _row_to_parametres_legals(row: sqlite3.Row) -> ParametresLegals:
    """Converteix una fila de la BD a un objecte ParametresLegals."""
    return ParametresLegals(
        descans_minim_hores=row["descans_minim_hores"],
        descans_minim_auxiliars_hores=row["descans_minim_auxiliars_hores"],
        llindar_torn_llarg_hores=row["llindar_torn_llarg_hores"],
        descans_torn_llarg_hores=row["descans_torn_llarg_hores"],
        dies_periode_descans_setmanal=row["dies_periode_descans_setmanal"],
    )


# ============================================================================
# FUNCIONS CRUD PER A VIGILANTS
# ============================================================================

def crear_vigilant(v: Vigilant) -> None:
    """Crea un nou vigilant a la base de dades."""
    with _connect() as conn:
        cursor = conn.cursor()
        row = _vigilant_to_row(v)
        
        cursor.execute("""
            INSERT INTO vigilants 
            (id, habilitacions, hores_objectiu_periode, hores_acumulades, 
             hores_max_setmana, zona_preferida, torn_preferit, actiu, 
             torns_no_desitjats, binomi_preferit)
            VALUES (:id, :habilitacions, :hores_objectiu_periode, :hores_acumulades,
                    :hores_max_setmana, :zona_preferida, :torn_preferit, :actiu,
                    :torns_no_desitjats, :binomi_preferit)
        """, row)
        
        # Guardar baixes
        for baixa_inici, baixa_fi in v.baixes:
            cursor.execute("""
                INSERT INTO baixes (vigilant_id, inici, fi)
                VALUES (?, ?, ?)
            """, (v.id, baixa_inici.isoformat(), baixa_fi.isoformat()))
        
        conn.commit()


def obtenir_vigilant(vigilant_id: str) -> Optional[Vigilant]:
    """Obté un vigilant per ID."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vigilants WHERE id = ?", (vigilant_id,))
        row = cursor.fetchone()
        if row:
            return _row_to_vigilant(row)
    return None


def obtenir_tots_vigilants() -> List[Vigilant]:
    """Obté tots els vigilants de la base de dades."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vigilants")
        return [_row_to_vigilant(row) for row in cursor.fetchall()]


def actualitzar_vigilant(v: Vigilant) -> None:
    """Actualitza un vigilant existent."""
    with _connect() as conn:
        cursor = conn.cursor()
        row = _vigilant_to_row(v)
        row["data_actualitzacio"] = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE vigilants SET
                habilitacions = :habilitacions,
                hores_objectiu_periode = :hores_objectiu_periode,
                hores_acumulades = :hores_acumulades,
                hores_max_setmana = :hores_max_setmana,
                zona_preferida = :zona_preferida,
                torn_preferit = :torn_preferit,
                actiu = :actiu,
                torns_no_desitjats = :torns_no_desitjats,
                binomi_preferit = :binomi_preferit,
                data_actualitzacio = :data_actualitzacio
            WHERE id = :id
        """, row)
        
        # Esborrar baixes antigues i inserir les noves
        cursor.execute("DELETE FROM baixes WHERE vigilant_id = ?", (v.id,))
        for baixa_inici, baixa_fi in v.baixes:
            cursor.execute("""
                INSERT INTO baixes (vigilant_id, inici, fi)
                VALUES (?, ?, ?)
            """, (v.id, baixa_inici.isoformat(), baixa_fi.isoformat()))
        
        conn.commit()


def esborrar_vigilant(vigilant_id: str) -> None:
    """Esborra un vigilant de la base de dades."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vigilants WHERE id = ?", (vigilant_id,))
        cursor.execute("DELETE FROM baixes WHERE vigilant_id = ?", (vigilant_id,))
        cursor.execute("DELETE FROM assignacions WHERE vigilant_id = ?", (vigilant_id,))
        cursor.execute("DELETE FROM historic_assignacions WHERE vigilant_id = ?", (vigilant_id,))
        conn.commit()


# ============================================================================
# FUNCIONS CRUD PER A SERVEIS
# ============================================================================

def crear_servei(s: Servei) -> None:
    """Crea un nou servei a la base de dades."""
    with _connect() as conn:
        cursor = conn.cursor()
        row = _servei_to_row(s)
        
        cursor.execute("""
            INSERT INTO serveis 
            (id, zona, inici, fi, habilitacio_requerida, vigilants_requerits, torn, binomi_obligatori)
            VALUES (:id, :zona, :inici, :fi, :habilitacio_requerida, :vigilants_requerits, :torn, :binomi_obligatori)
        """, row)
        conn.commit()


def obtenir_servei(servei_id: str) -> Optional[Servei]:
    """Obté un servei per ID."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM serveis WHERE id = ?", (servei_id,))
        row = cursor.fetchone()
        if row:
            return _row_to_servei(row)
    return None


def obtenir_tots_serveis(
    data_inici: Optional[datetime] = None,
    data_fi: Optional[datetime] = None
) -> List[Servei]:
    """Obté tots els serveis de la base de dades (opcionalment filtrats per dates)."""
    with _connect() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM serveis"
        params = []
        
        if data_inici and data_fi:
            query += " WHERE inici BETWEEN ? AND ?"
            params.extend([data_inici.isoformat(), data_fi.isoformat()])
        elif data_inici:
            query += " WHERE inici >= ?"
            params.append(data_inici.isoformat())
        elif data_fi:
            query += " WHERE fi <= ?"
            params.append(data_fi.isoformat())
        
        query += " ORDER BY inici"
        cursor.execute(query, params)
        return [_row_to_servei(row) for row in cursor.fetchall()]


def actualitzar_servei(s: Servei) -> None:
    """Actualitza un servei existent."""
    with _connect() as conn:
        cursor = conn.cursor()
        row = _servei_to_row(s)
        
        cursor.execute("""
            UPDATE serveis SET
                zona = :zona,
                inici = :inici,
                fi = :fi,
                habilitacio_requerida = :habilitacio_requerida,
                vigilants_requerits = :vigilants_requerits,
                torn = :torn,
                binomi_obligatori = :binomi_obligatori
            WHERE id = :id
        """, row)
        conn.commit()


def esborrar_servei(servei_id: str) -> None:
    """Esborra un servei de la base de dades."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM serveis WHERE id = ?", (servei_id,))
        cursor.execute("DELETE FROM assignacions WHERE servei_id = ?", (servei_id,))
        cursor.execute("DELETE FROM historic_assignacions WHERE servei_id = ?", (servei_id,))
        conn.commit()


# ============================================================================
# FUNCIONS PER A ASSIGNACIONS
# ============================================================================

def obtenir_assignacions_actuals() -> Dict[Tuple[str, str], bool]:
    """Obté totes les assignacions actuals (publicades i no publicades).
    
    Retorna:
        Diccionari {(vigilant_id, servei_id): publicat}
    """
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT vigilant_id, servei_id, publicat FROM assignacions")
        return {
            (row["vigilant_id"], row["servei_id"]): bool(row["publicat"])
            for row in cursor.fetchall()
        }


def obtenir_assignacions_publicades() -> Dict[Tuple[str, str], bool]:
    """Obté només les assignacions publicades.
    
    Retorna:
        Diccionari {(vigilant_id, servei_id): True}
    """
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT vigilant_id, servei_id FROM assignacions WHERE publicat = 1")
        return {
            (row["vigilant_id"], row["servei_id"]): True
            for row in cursor.fetchall()
        }


def obtenir_assignacions_temptatives() -> Dict[Tuple[str, str], bool]:
    """Obté només les assignacions temptatives (no publicades).
    
    Retorna:
        Diccionari {(vigilant_id, servei_id): True}
    """
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT vigilant_id, servei_id FROM assignacions WHERE publicat = 0")
        return {
            (row["vigilant_id"], row["servei_id"]): True
            for row in cursor.fetchall()
        }


def guardar_assignacions(
    assignacions: List[Tuple[str, str]],
    publicat: bool = False
) -> None:
    """Guarda assignacions a la base de dades.
    
    Args:
        assignacions: Llista de tuples (vigilant_id, servei_id).
        publicat: Si True, marca les assignacions com a publicades.
    """
    with _connect() as conn:
        cursor = conn.cursor()
        
        # Esborrar assignacions no publicades (les publicades es mantenen)
        if not publicat:
            cursor.execute("DELETE FROM assignacions WHERE publicat = 0")
        
        # Inserir noves assignacions
        for v_id, s_id in assignacions:
            cursor.execute("""
                INSERT INTO assignacions (vigilant_id, servei_id, publicat)
                VALUES (?, ?, ?)
                ON CONFLICT(vigilant_id, servei_id) DO UPDATE SET
                    publicat = MAX(assignacions.publicat, excluded.publicat)
            """, (v_id, s_id, int(publicat)))
        
        conn.commit()


def publicar_assignacions(servei_ids: List[str]) -> None:
    """Marca assignacions com a publicades.
    
    Args:
        servei_ids: Llista d'IDs de serveis a publicar.
    """
    with _connect() as conn:
        cursor = conn.cursor()
        for s_id in servei_ids:
            cursor.execute("""
                UPDATE assignacions SET publicat = 1 
                WHERE servei_id = ?
            """, (s_id,))
            cursor.execute("""
                INSERT INTO historic_assignacions (vigilant_id, servei_id, motiu)
                SELECT a.vigilant_id, a.servei_id, 'publicació'
                FROM assignacions a
                WHERE a.servei_id = ? AND a.publicat = 1
                  AND NOT EXISTS (
                      SELECT 1 FROM historic_assignacions h
                      WHERE h.vigilant_id = a.vigilant_id
                        AND h.servei_id = a.servei_id
                        AND h.data_desassignacio IS NULL
                  )
            """, (s_id,))
            if cursor.rowcount:
                cursor.execute("""
                    UPDATE vigilants
                    SET hores_acumulades = hores_acumulades + COALESCE((
                        SELECT SUM((julianday(s.fi) - julianday(s.inici)) * 24.0)
                        FROM assignacions a
                        JOIN serveis s ON s.id = a.servei_id
                        WHERE a.vigilant_id = vigilants.id
                          AND a.servei_id = ?
                          AND a.publicat = 1
                    ), 0)
                    WHERE id IN (
                        SELECT vigilant_id FROM assignacions
                        WHERE servei_id = ? AND publicat = 1
                    )
                """, (s_id, s_id))
        conn.commit()


def obtenir_hores_acumulades(vigilant_id: str) -> float:
    """Obté les hores acumulades persistides del vigilant."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT hores_acumulades FROM vigilants WHERE id = ?",
            (vigilant_id,),
        )
        row = cursor.fetchone()
        return float(row["hores_acumulades"]) if row else 0.0


# ============================================================================
# FUNCIONS PER A SUBSTITUCIONS D'URGÈNCIA
# ============================================================================

def registrar_substitucio(
    servei_id: str,
    vigilant_original: Optional[str],
    vigilant_substitut: str,
    motiu: str,
    candidats_avaluats: List[Dict] = None
) -> None:
    """Registra una substitució d'urgència a l'històric.
    
    Args:
        servei_id: ID del servei que s'ha substituït.
        vigilant_original: ID del vigilant original (None si no n'hi havia).
        vigilant_substitut: ID del vigilant substitut.
        motiu: Motiu de la substitució (ex: "baixa", "malaltia").
        candidats_avaluats: Llista de candidats avaluats (per a audit).
    """
    import json
    
    with _connect() as conn:
        cursor = conn.cursor()
        
        # Inserir a historic_substitucions
        cursor.execute("""
            INSERT INTO historic_substitucions 
            (servei_id, vigilant_original, vigilant_substitut, motiu, candidats_avaluats)
            VALUES (?, ?, ?, ?, ?)
        """, (
            servei_id,
            vigilant_original,
            vigilant_substitut,
            motiu,
            json.dumps(candidats_avaluats) if candidats_avaluats else None
        ))
        
        # Actualitzar assignacions
        if vigilant_original:
            # Desassignar l'original (si existia)
            cursor.execute("""
                INSERT INTO historic_assignacions 
                (vigilant_id, servei_id, data_desassignacio, motiu)
                VALUES (?, ?, ?, ?)
            """, (
                vigilant_original,
                servei_id,
                datetime.now().isoformat(),
                f"Substitució: {motiu}"
            ))
            cursor.execute(
                "DELETE FROM assignacions WHERE vigilant_id = ? AND servei_id = ?",
                (vigilant_original, servei_id)
            )
        
        # Assignar el substitut
        cursor.execute("""
            INSERT OR REPLACE INTO assignacions 
            (vigilant_id, servei_id, publicat)
            VALUES (?, ?, 1)
        """, (vigilant_substitut, servei_id))
        
        cursor.execute("""
            INSERT INTO historic_assignacions 
            (vigilant_id, servei_id, motiu)
            VALUES (?, ?, ?)
        """, (vigilant_substitut, servei_id, f"Substitució: {motiu}"))
        
        conn.commit()


# ============================================================================
# FUNCIONS PER A PARAMETRES LEGALS
# ============================================================================

def obtenir_parametres_legals() -> ParametresLegals:
    """Obté els paràmetres legals actius."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM parametres_legals WHERE actiu = 1 LIMIT 1")
        row = cursor.fetchone()
        if row:
            return _row_to_parametres_legals(row)
    return ParametresLegals()


def actualitzar_parametres_legals(params: ParametresLegals) -> None:
    """Actualitza els paràmetres legals."""
    with _connect() as conn:
        cursor = conn.cursor()
        
        # Desactivar els antics
        cursor.execute("UPDATE parametres_legals SET actiu = 0")
        
        # Inserir els nous
        cursor.execute("""
            INSERT INTO parametres_legals 
            (descans_minim_hores, descans_minim_auxiliars_hores, 
             llindar_torn_llarg_hores, descans_torn_llarg_hores, 
             dies_periode_descans_setmanal, actiu)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (
            params.descans_minim_hores,
            params.descans_minim_auxiliars_hores,
            params.llindar_torn_llarg_hores,
            params.descans_torn_llarg_hores,
            params.dies_periode_descans_setmanal,
        ))
        conn.commit()


# ============================================================================
# FUNCIONS PER A ESTADÍSTIQUES
# ============================================================================

def guardar_estadistiques(
    total_serveis: int,
    serveis_coberts: int,
    serveis_sense_cobertura: int,
    vigilants_actius: int,
    vigilants_assignats: int,
    mitjana_hores: float,
    max_hores: float,
    min_hores: float
) -> None:
    """Guarda estadístiques a la base de dades."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO estadistiques 
            (total_serveis, serveis_coberts, serveis_sense_cobertura, 
             vigilants_actius, vigilants_assignats, mitjana_hores, max_hores, min_hores)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            total_serveis,
            serveis_coberts,
            serveis_sense_cobertura,
            vigilants_actius,
            vigilants_assignats,
            mitjana_hores,
            max_hores,
            min_hores,
        ))
        conn.commit()


# ============================================================================
# FUNCIONS D'UTILITAT
# ============================================================================

def importar_dades_exemple() -> None:
    """Importa les dades d'exemple a la base de dades."""
    from dades_exemple import genera_vigilants, genera_serveis
    
    vigilants = genera_vigilants()
    serveis = genera_serveis(dies=14)  # 14 dies per a rolling horizon
    
    with _connect() as conn:
        cursor = conn.cursor()
        
        # Esborrar dades existents
        cursor.execute("DELETE FROM vigilants")
        cursor.execute("DELETE FROM serveis")
        cursor.execute("DELETE FROM assignacions")
        cursor.execute("DELETE FROM baixes")
        cursor.execute("DELETE FROM historic_assignacions")
        cursor.execute("DELETE FROM historic_substitucions")
        cursor.execute("DELETE FROM rolling_horizon_estat")
        
        # Inserir vigilants
        for v in vigilants:
            row = _vigilant_to_row(v)
            cursor.execute("""
                INSERT INTO vigilants 
                (id, habilitacions, hores_objectiu_periode, hores_acumulades, 
                 hores_max_setmana, zona_preferida, torn_preferit, actiu, 
                 torns_no_desitjats, binomi_preferit)
                VALUES (:id, :habilitacions, :hores_objectiu_periode, :hores_acumulades,
                        :hores_max_setmana, :zona_preferida, :torn_preferit, :actiu,
                        :torns_no_desitjats, :binomi_preferit)
            """, row)
            
            # Inserir baixes
            for baixa_inici, baixa_fi in v.baixes:
                cursor.execute("""
                    INSERT INTO baixes (vigilant_id, inici, fi)
                    VALUES (?, ?, ?)
                """, (v.id, baixa_inici.isoformat(), baixa_fi.isoformat()))
        
        # Inserir serveis
        for s in serveis:
            row = _servei_to_row(s)
            cursor.execute("""
                INSERT INTO serveis 
                (id, zona, inici, fi, habilitacio_requerida, vigilants_requerits, torn, binomi_obligatori)
                VALUES (:id, :zona, :inici, :fi, :habilitacio_requerida, :vigilants_requerits, :torn, :binomi_obligatori)
            """, row)
        
        conn.commit()
    
    print(f"✅ Importats {len(vigilants)} vigilants i {len(serveis)} serveis a la base de dades.")


def obtenir_estat_rolling_horizon() -> Optional[Dict]:
    """Obté l'estat actual de l'horitzó mòbil."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rolling_horizon_estat ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def guardar_estat_rolling_horizon(
    data_inici: datetime,
    data_fi: datetime,
    finestra_actual: int,
    dies_publicats: int,
    temps_resolucio_segons: float,
    estat_solver: str
) -> None:
    """Guarda l'estat de l'horitzó mòbil."""
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO rolling_horizon_estat 
            (data_inici, data_fi, finestra_actual, dies_publicats, 
             data_ultima_resolucio, temps_resolucio_segons, estat_solver)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data_inici.isoformat(),
            data_fi.isoformat(),
            finestra_actual,
            dies_publicats,
            datetime.now().isoformat(),
            temps_resolucio_segons,
            estat_solver
        ))
        conn.commit()


# Inicialitzar la base de dades al carregar el mòdul
init_db()
