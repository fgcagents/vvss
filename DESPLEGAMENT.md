# \ud83c\udfe2 **Guia de Desplegament - Sistema VVSS**

> **Guia completa per a instal\u00b7lar, configurar i desplegar el sistema VVSS en entorns de desenvolupament i producci\u00f3**

---

## \ud83d\udcc1 **\u00cdndex**

1. [Requisits del Sistema](#-requisits-del-sistema)
2. [Instal\u00b7laci\u00f3](#-instal\u00b7laci\u00f3)
3. [Configuraci\u00f3 Inicial](#-configuraci\u00f3-inicial)
4. [Base de Dades SQLite](#-base-de-dades-sqlite)
5. [Execuci\u00f3 del Sistema](#-execuci\u00f3-del-sistema)
6. [Configuraci\u00f3 Avan\u00e7ada](#-configuraci\u00f3-avan\u00e7ada)
7. [Desplegament en Producci\u00f3](#-desplegament-en-producci\u00f3)
8. [Monitoritzaci\u00f3 i Manteniment](#-monitoritzaci\u00f3-i-manteniment)
9. [Solució de Problemres](#-solució-de-problemres)
10. [Backup i Restauraci\u00f3](#-backup-i-restauraci\u00f3)
11. [Actualitzacions](#-actualitzacions)

---

## \ud83d\udccf **\u26a0\ufe0f Requisits del Sistema**

### **Requisits M\u00ednims**

| **Component** | **Requisit** | **Recomanat** | **Notes** |
|--------------|--------------|---------------|-----------|
| **Sistema Operatiu** | Linux, macOS, Windows | Ubuntu 22.04 LTS | Qualsevol SO modern |
| **Python** | 3.10+ | 3.12 | OR-Tools requereix Python 3.10 o superior |
| **RAM** | 2 GB | 8 GB+ | Dep\u00e8n de la mida del problema |
| **CPU** | 2 n\u00bacleus | 8+ n\u00bacleus | M\u00e9s n\u00bacleus = resoluci\u00f3 m\u00e9s r\u00e0pida |
| **Disc Dur** | 500 MB | 1 GB+ | Per a la base de dades i logs |
| **OR-Tools** | 9.5+ | 9.9+ | Versi\u00f3 m\u00e9s recent |

### **Requisits de Software**

```bash
# Depend\u00e8ncies obligat\u00f2ries
python >= 3.10
pip >= 23.0

# Depend\u00e8ncies Python
ortools >= 9.5.2237
pydantic >= 2.5.0
pandas >= 2.0.0
```

### **Matriu de Compatibilitat**

| **Python** | **OR-Tools** | **Pydantic** | **Pandas** | **Estat** |
|------------|--------------|--------------|-----------|-----------|
| 3.10 | 9.5+ | 2.5+ | 2.0+ | \u2705 Suportat |
| 3.11 | 9.5+ | 2.5+ | 2.0+ | \u2705 Suportat |
| 3.12 | 9.9+ | 2.5+ | 2.0+ | \u2705 Recomanat |

---

## \ud83d\udccf **\u2705 Instal\u00b7laci\u00f3**

### **Oci\u00f3 1: Instal\u00b7laci\u00f3 R\u00e0pida (Desenvolupament)**

```bash
# 1. Clonar el repositori
git clone https://github.com/fgcagents/vvss.git
cd vvss

# 2. Crear entorn virtual (opcional per\u00f2 recomanat)
python -m venv venv

# 3. Activar l'entorn
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. Instal\u00b7lar depend\u00e8ncies
pip install -r requirements.txt

# 5. Verificar instal\u00b7laci\u00f3
python -c "import ortools; print(f'OR-Tools: {ortools.__version__}')"
python -c "import pydantic; print(f'Pydantic: {pydantic.__version__}')"
python -c "import pandas; print(f'Pandas: {pandas.__version__}')"
```

### **Oci\u00f3 2: Instal\u00b7laci\u00f3 en Producci\u00f3 (Linux Server)**

```bash
# 1. Crear usuari dedicat
sudo useradd -r -m -d /opt/vvss -s /bin/bash vvss
sudo usermod -aG sudo vvss

# 2. Instal\u00b7lar Python i depend\u00e8ncies del sistema
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev git sqlite3

# 3. Clonar el repositori
sudo -u vvss git clone https://github.com/fgcagents/vvss.git /opt/vvss

# 4. Crear entorn virtual
sudo -u vvss python3.12 -m venv /opt/vvss/venv

# 5. Instal\u00b7lar depend\u00e8ncies
sudo -u vvss /opt/vvss/venv/bin/pip install -r /opt/vvss/requirements.txt

# 6. Configurar permissos
sudo chown -R vvss:vvss /opt/vvss
sudo chmod -R 750 /opt/vvss
```

### **Oci\u00f3 3: Instal\u00b7laci\u00f3 amb Docker (Recomanat per Producci\u00f3)**

#### **Dockerfile**

```dockerfile
# Dockerfile per a VVSS
FROM python:3.12-slim

# Configurar entorn
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instal\u00b7lar depend\u00e8ncies del sistema
RUN apt-get update && apt-get install -y \
    git \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instal\u00b7lar depend\u00e8ncies Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codi font
COPY . .

# Crear base de dades inicial
RUN python -c "from database import reset_db; reset_db()"

# Exposar port (opcional per a API futura)
EXPOSE 8000

# Comanda per defecte
CMD ["python", "main.py"]
```

#### **docker-compose.yml**

```yaml
version: '3.8'

services:
  vvss:
    build: .
    container_name: vvss
    volumes:
      - ./vvss.db:/app/vvss.db
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    # Per a entorns amb GPU (opcional)
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]
```

#### **Comandes Docker**

```bash
# Construir la imatge
docker-compose build

# Iniciar el servei
docker-compose up -d

# Veure logs
docker-compose logs -f vvss

# Aturar el servei
docker-compose down

# Actualitzar
docker-compose pull && docker-compose up -d --build
```

---

## \u2699 **\u2699 Configuraci\u00f3 Inicial**

### **Configuraci\u00f3 de l'Entorn**

#### **Variables d'Entorn**

```bash
# Variables d'entorn recomanades (opcional)
export VVSS_DB_PATH="/path/to/vvss.db"
export VVSS_MAX_WORKERS=8
export VVSS_TIME_LIMIT=30.0
export VVSS_LOG_LEVEL="INFO"
```

#### **Fitxer .env (Opcional)**

```bash
# .env
VVSS_DB_PATH=./vvss.db
VVSS_MAX_WORKERS=8
VVSS_TIME_LIMIT=30.0
VVSS_LOG_LEVEL=INFO
VVSS_ENABLE_DEBUG=False
```

### **Configuraci\u00f3 de la Base de Dades**

Veure [Secci\u00f3 de Base de Dades](#-base-de-dades-sqlite) per a m\u00e9s detalls.

---

## \ud83c\udf80 **\u2699 Base de Dades SQLite**

### **Estructura de la Base de Dades**

El sistema utilitza **SQLite 3** per a la persist\u00e8ncia de dades. La base de dades cont\u00e9 les següents taules:

| **Taula** | **Descripci\u00f3** | **Relacions** |
|-----------|----------------|---------------|
| `vigilants` | Informaci\u00f3 dels vigilants | - |
| `serveis` | Definici\u00f3 dels serveis | - |
| `assignacions` | Assignacions actuals | vigilants, serveis |
| `baixes` | Baixes m\u00e8diques | vigilants |
| `historic_assignacions` | Hist\u00f2ric d'assignacions | vigilants, serveis |
| `historic_substitucions` | Hist\u00f2ric de substitucions | vigilants, serveis |
| `parametres_legals` | Par\u00e0metres legals | - |
| `rolling_horizon_estat` | Estat del Rolling Horizon | - |
| `estadistiques` | Estad\u00edstiques del sistema | - |
| `motius_descobert` | Motius de descoberts | - |
| `descoberts` | Registre de descoberts | serveis, motius_descobert |

### **Inicialitzaci\u00f3 de la Base de Dades**

```python
# Importar i inicialitzar
from database import reset_db, init_db

# Oci\u00f3 1: Reiniciar la base de dades (esborra tot!)
reset_db()

# Oci\u00f3 2: Inicialitzar amb dades d'exemple
from dades_exemple import generar_dades_exemple
dades = generar_dades_exemple()
init_db(dades)
```

### **Ubicaci\u00f3 de la Base de Dades**

Per defecte, la base de dades es crea a `./vvss.db`. Per a canviar la ubicaci\u00f3:

```python
# A database.py, modificar:
DB_PATH = "/path/to/vvss.db"
```

O amb variable d'entorn:

```bash
export VVSS_DB_PATH="/path/to/vvss.db"
```

### **Esquema de la Base de Dades**

#### **Taula: vigilants**

```sql
CREATE TABLE vigilants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    identificador TEXT UNIQUE NOT NULL,
    hores_max_setmana INTEGER DEFAULT 48,
    hores_max_dia INTEGER DEFAULT 9,
    dies_max_consecutius INTEGER DEFAULT 6,
    cert_cctv BOOLEAN DEFAULT FALSE,
    cert_armes BOOLEAN DEFAULT FALSE,
    cert_nit BOOLEAN DEFAULT FALSE,
    senior BOOLEAN DEFAULT FALSE,
    actiu BOOLEAN DEFAULT TRUE,
    data_alta TEXT,
    data_baixa TEXT,
    idiomes TEXT,
    preferencies TEXT,
    UNIQUE(identificador)
);
```

#### **Taula: serveis**

```sql
CREATE TABLE serveis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codi TEXT UNIQUE NOT NULL,
    nom TEXT NOT NULL,
    tipus TEXT NOT NULL CHECK(tipus IN ('estacio', 'patrulla', 'binomi')),
    estacio TEXT,
    dia INTEGER NOT NULL,
    torn TEXT NOT NULL CHECK(torn IN ('matí', 'tarda', 'nit')),
    hora_inici TEXT NOT NULL,
    hora_fi TEXT NOT NULL,
    durada_hores REAL NOT NULL,
    binomi_obligatori BOOLEAN DEFAULT FALSE,
    requereix_cctv BOOLEAN DEFAULT FALSE,
    requereix_armes BOOLEAN DEFAULT FALSE,
    prioritat INTEGER DEFAULT 1,
    actiu BOOLEAN DEFAULT TRUE,
    UNIQUE(codi, dia)
);
```

#### **Taula: assignacions**

```sql
CREATE TABLE assignacions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vigilant_id INTEGER NOT NULL,
    servei_id INTEGER NOT NULL,
    dia INTEGER NOT NULL,
    torn TEXT NOT NULL,
    hores REAL NOT NULL,
    assignat_automatic BOOLEAN DEFAULT TRUE,
    data_assignacio TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vigilant_id) REFERENCES vigilants(id),
    FOREIGN KEY (servei_id) REFERENCES serveis(id),
    UNIQUE(vigilant_id, servei_id, dia)
);
```

### **Scripts de Manteniment**

#### **Backup de la Base de Dades**

```bash
# Crear backup
sqlite3 vvss.db ".backup vvss_backup_$(date +%Y%m%d_%H%M%S).db"

# O amb Python
import sqlite3
import shutil
from datetime import datetime

conn = sqlite3.connect('vvss.db')
backup_name = f"vvss_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
shutil.copy2('vvss.db', backup_name)
conn.close()
```

#### **Restauraci\u00f3 de Backup**

```bash
# Restaurar des de backup
sqlite3 vvss.db ".restore vvss_backup.db"

# O amb Python
import shutil
shutil.copy2('vvss_backup.db', 'vvss.db')
```

#### **Optimitzaci\u00f3 de la Base de Dades**

```bash
# Optimitzar i netejar
sqlite3 vvss.db "VACUUM;"
sqlite3 vvss.db "REINDEX;"
sqlite3 vvss.db "ANALYZE;"
```

---

## \ud83d\ude80 **\u2699 Execuci\u00f3 del Sistema**

### **Execuci\u00f3 B\u00e0sica**

```bash
# Executar el sistema principal
python main.py

# Executar amb par\u00e0metres personalitzats
python -c "
from database import reset_db
from integrated_system import SistemaIntegrat

# Reiniciar base de dades
reset_db()

# Crear sistema integrat
sistema = SistemaIntegrat(
    dies_finestra=5,      # Dies per finestra
    dies_lookback=2,      # Dies de lookback
    dies_horitzo_total=14 # Dies totals
)

# Inicialitzar amb dades d'exemple
sistema.inicialitzar_sistema()

# Executar Rolling Horizon
sistema.executar_rolling_horizon()
"
```

### **Execuci\u00f3 amb Dades Reals**

```python
# Exemple: Carregar dades reals des de fitxers
from database import importar_dades_desde_csv

# Importar vigilants des de CSV
importar_dades_desde_csv(
    vigilants_csv='vigilants.csv',
    serveis_csv='serveis.csv'
)

# Executar el sistema
from integrated_system import SistemaIntegrat

sistema = SistemaIntegrat(dies_finestra=7, dies_lookback=3, dies_horitzo_total=30)
sistema.inicialitzar_sistema()
sistema.executar_rolling_horizon()
```

### **Execuci\u00f3 en Mode Debug**

```bash
# Activar mode debug
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)

from integrated_system import SistemaIntegrat

sistema = SistemaIntegrat(
    dies_finestra=3,
    dies_lookback=1,
    dies_horitzo_total=7
)
sistema.inicialitzar_sistema()
sistema.executar_rolling_horizon()
" 2>&1 | tee debug.log
```

### **Execuci\u00f3 amb Par\u00e0metres del Solver**

```python
from integrated_system import SistemaIntegrat
from ortools.sat.python import cp_model

sistema = SistemaIntegrat(
    dies_finestra=5,
    dies_lookback=2,
    dies_horitzo_total=14
)

# Configurar par\u00e0metres del solver
sistema.model_builder.solver.parameters.max_time_in_seconds = 30.0
sistema.model_builder.solver.parameters.num_workers = 16
sistema.model_builder.solver.parameters.log_search_progress = True

sistema.inicialitzar_sistema()
sistema.executar_rolling_horizon()
```

---

## \u2699 **\u2699 Configuraci\u00f3 Avan\u00e7ada**

### **Par\u00e0metres del Model**

#### **Par\u00e0metres Legals (database.py)**

```python
# Valors per defecte (compliment normativa espanyola)
PARAMETRES_LEGALS = {
    "descans_minim_hores": 13.0,           # Hores de descans entre torns
    "descans_minim_auxiliars_hores": 12.0, # Per a vigilants auxiliars
    "llindar_torn_llarg_hores": 20.0,      # Torn considerat llarg
    "descans_torn_llarg_hores": 48.0,     # Descans despr\u00e9s de torn llarg
    "dies_periode_descans_setmanal": 7,    # 1 dia lliure cada 7 dies
    "hores_max_setmana": 48,              # M\u00e0xim 48h/setmana
    "hores_max_dia": 9,                  # M\u00e0xim 9h/dia
    "dies_max_consecutius": 6,           # M\u00e0xim 6 dies consecutius
}
```

#### **Par\u00e0metres del Solver (solver.py)**

```python
# Configuraci\u00f3 del CP-SAT Solver
solver.parameters.max_time_in_seconds = 10.0   # Temps l\u00edmit per resoluci\u00f3
solver.parameters.num_workers = 8              # Processament en paral\u00b7lel
solver.parameters.log_search_progress = True   # Mostrar progr\u00e9s
solver.parameters.cp_model_presolve = True     # Pre-resoluci\u00f3
solver.parameters.cp_model_use_sat = True      # Usar SAT solver
```

#### **Par\u00e0metres del Rolling Horizon (integrated_system.py)**

```python
# Configuraci\u00f3 del sistema integrat
sistema = SistemaIntegrat(
    dies_finestra=5,           # Mida de la finestra (dies)
    dies_lookback=2,           # Dies de lookback per a equitat
    dies_horitzo_total=14,     # Dies totals a planificar
    max_descoberts_acceptats=0, # M\u00e0xim de descoberts acceptats
    pes_equilibri_hores=10,    # Pes per a equilibri d'hores
    pes_preferencia=1,         # Pes per a prefer\u00e8ncies
    pes_equitat_nits=20,       # Pes per a equitat de nits
    pes_cobertura=1000,        # Pes per a cobertura (hard constraint)
    pes_torn_no_desitjat=50    # Penalitzaci\u00f3 per torns no desitjats
)
```

### **Configuraci\u00f3 de la Funci\u00f3 Objectiu**

La funci\u00f3 objectiu es configura a `builder.py` i utilitza els següents pesos:

```python
# Pesos de la funci\u00f3 objectiu (modificables)
PESOS = {
    "cobertura": 1000,        # Prioritat m\u00e0xima: cobertura total
    "equilibri_hores": 10,    # Equilibri en la distribució d'hores
    "equitat_nits": 20,       # Equitat en la distribució de nits
    "preferencies": 1,        # Compliment de prefer\u00e8ncies
    "torn_no_desitjat": 50,   # Penalitzaci\u00f3 per torns no desitjats
    "binomi_preferit": 5,     # Prefer\u00e8ncia per binomis coneguts
}
```

### **Configuraci\u00f3 de la Gesti\u00f3 de Descoberts**

```python
# A descoberts_manager.py
GESTIO_DESCOBERTS = {
    "auto_resoldre": True,              # Intentar resoldre autom\u00e0ticament
    "notificar_critics": True,         # Notificar descoberts cr\u00edtics
    "registrar_tot": True,              # Registrar tots els descoberts
    "generar_informes": True,          # Generar informes peri\u00f2dics
    "monitoritzar": True,               # Monitoritzar descoberts
    "dies_lookback_informe": 7,         # Dies per a informes
}
```

---

## \ud83c\udf03 **\u2699 Desplegament en Producci\u00f3**

### **Requisits per a Producci\u00f3**

- **Servidor dedicat** (recomanat: 8+ CPU, 16+ GB RAM)
- **Sistema operatiu** estable (Ubuntu Server 22.04 LTS recomanat)
- **Monitoritzaci\u00f3** (Prometheus + Grafana opcional)
- **Backup autom\u00e0tic** (cron jobs)
- **Logging** centralitzat (ELK Stack opcional)

### **Arquitectura Recomanada**

```
┌─────────────────────────────────────────────────────────────┐
│                    Servidor de Producció                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐    │
│  │  VVSS App   │    │  SQLite     │    │  Backup System   │    │
│  │  (Python)   │───▶│  Database    │───▶│  (Automàtic)     │    │
│  └─────────────┘    └─────────────┘    └─────────────────┘    │
│       ▲                  ▲                  ▲                 │
│       │                  │                  │                 │
│  ┌────┴─────┐      ┌────┴─────┐      ┌────┴─────┐           │
│  │  Input    │      │  Output   │      │  Logs    │           │
│  │  Files    │      │  Files    │      │          │           │
│  └──────────┘      └──────────┘      └──────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### **Script de Desplegament Autom\u00e0tic**

```bash
#!/bin/bash
# deploy_vvss.sh

set -e

# Colors per a output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funcions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# 1. Instal\u00b7lar depend\u00e8ncies del sistema
log_info "Instal\u00b7lant depend\u00e8ncies del sistema..."
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev git sqlite3

# 2. Crear usuari
log_info "Creant usuari vvss..."
if ! id "vvss" &>/dev/null; then
    sudo useradd -r -m -d /opt/vvss -s /bin/bash vvss
    sudo usermod -aG sudo vvss
fi

# 3. Clonar repositori
log_info "Clonant repositori..."
sudo -u vvss git clone https://github.com/fgcagents/vvss.git /opt/vvss

# 4. Crear entorn virtual
log_info "Creant entorn virtual..."
sudo -u vvss python3.12 -m venv /opt/vvss/venv

# 5. Instal\u00b7lar depend\u00e8ncies Python
log_info "Instal\u00b7lant depend\u00e8ncies Python..."
sudo -u vvss /opt/vvss/venv/bin/pip install -r /opt/vvss/requirements.txt

# 6. Configurar permissos
log_info "Configurant permissos..."
sudo chown -R vvss:vvss /opt/vvss
sudo chmod -R 750 /opt/vvss

# 7. Crear servei systemd
log_info "Creant servei systemd..."
sudo tee /etc/systemd/system/vvss.service > /dev/null << 'EOF'
[Unit]
Description=VVSS - Sistema d'Assignacio de Vigilants
After=network.target

[Service]
Type=simple
User=vvss
Group=vvss
WorkingDirectory=/opt/vvss
Environment="PATH=/opt/vvss/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/opt/vvss/venv/bin/python /opt/vvss/main.py
Restart=always
RestartSec=30

# Configuraci\u00f3 de recursos
MemoryLimit=4G
CPUQuota=50%

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=vvss

[Install]
WantedBy=multi-user.target
EOF

# 8. Habilitar i iniciar servei
log_info "Habilitant i iniciant servei..."
sudo systemctl daemon-reload
sudo systemctl enable vvss.service
sudo systemctl start vvss.service

# 9. Verificar estat
log_info "Verificant estat del servei..."
sudo systemctl status vvss.service

# 10. Configurar backup autom\u00e0tic
log_info "Configurant backup autom\u00e0tic..."
sudo tee /etc/cron.daily/vvss_backup > /dev/null << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/vvss"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
cp /opt/vvss/vvss.db "$BACKUP_DIR/vvss_$DATE.db"

# Mantenir \u00faltims 30 backups
cd "$BACKUP_DIR" && ls -t | tail -n +31 | xargs rm -f
EOF

sudo chmod +x /etc/cron.daily/vvss_backup

log_info "Desplegament completat amb \u00e8xit!"
```

### **Configuraci\u00f3 de Systemd**

#### **Fitxer de servei: /etc/systemd/system/vvss.service**

```ini
[Unit]
Description=VVSS - Sistema d'Assignacio de Vigilants per a FGC
After=network.target

[Service]
Type=simple
User=vvss
Group=vvss
WorkingDirectory=/opt/vvss
Environment="PATH=/opt/vvss/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="VVSS_DB_PATH=/opt/vvss/vvss.db"
Environment="VVSS_MAX_WORKERS=16"
Environment="VVSS_TIME_LIMIT=60.0"
ExecStart=/opt/vvss/venv/bin/python /opt/vvss/main.py
Restart=always
RestartSec=30

# L\u00edmits de recursos
MemoryLimit=8G
MemoryMax=12G
CPUQuota=80%

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=vvss

# Health check (opcional)
ExecStartPost=/bin/sh -c 'until /opt/vvss/venv/bin/python -c "import sqlite3; conn = sqlite3.connect(\"/opt/vvss/vvss.db\"); conn.execute(\"SELECT 1\"); conn.close()"; do sleep 1; done'

[Install]
WantedBy=multi-user.target
```

#### **Comandes de Systemd**

```bash
# Iniciar el servei
sudo systemctl start vvss

# Aturar el servei
sudo systemctl stop vvss

# Reiniciar el servei
sudo systemctl restart vvss

# Veure estat
sudo systemctl status vvss

# Veure logs
sudo journalctl -u vvss -f

# Habilitar a l'arrencada
sudo systemctl enable vvss

# Deshabilitar a l'arrencada
sudo systemctl disable vvss
```

---

## \ud83d\udcc8 **\u2699 Monitoritzaci\u00f3 i Manteniment**

### **Monitoritzaci\u00f3 B\u00e0sica**

```bash
# Veure logs en temps real
sudo journalctl -u vvss -f

# Veure logs hist\u00f2rics
sudo journalctl -u vvss --since "2024-01-01" --until "2024-01-31"

# Veure \u00faltimes 100 l\u00ednies de log
sudo journalctl -u vvss -n 100

# Veure estat del servei
sudo systemctl status vvvss

# Veure \u00fas de CPU i mem\u00f2ria
sudo systemctl status vvss -l | grep -E "CPU|Memory"
```

### **Monitoritzaci\u00f3 Avan\u00e7ada (Prometheus + Grafana)**

#### **1. Instal\u00b7lar Node Exporter**

```bash
# Instal\u00b7lar Node Exporter per a m\u00e8triques del sistema
wget https://github.com/prometheus/node_exporter/releases/download/v1.5.0/node_exporter-1.5.0.linux-amd64.tar.gz
tar xvfz node_exporter-1.5.0.linux-amd64.tar.gz
cd node_exporter-1.5.0.linux-amd64

# Crear servei systemd
sudo tee /etc/systemd/system/node_exporter.service > /dev/null << 'EOF'
[Unit]
Description=Node Exporter
After=network.target

[Service]
Type=simple
ExecStart=/opt/node_exporter/node_exporter
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable node_exporter
sudo systemctl start node_exporter
```

#### **2. Configurar Prometheus**

```yaml
# /etc/prometheus/prometheus.yml
scrape_configs:
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'vvss'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

#### **3. Crear M\u00e8triques Personalitzades per a VVSS**

```python
# A main.py o integrated_system.py
from prometheus_client import start_http_server, Counter, Gauge, Histogram
import time

# Inicialitzar m\u00e8triques
SERVEIS_COBERTS = Gauge('vvss_serveis_coberts', 'Nombre de serveis coberts')
SERVEIS_DESCOBERTS = Gauge('vvss_serveis_descoberts', 'Nombre de serveis descoberts')
TEMPS_RESOLUCIO = Histogram('vvss_temps_resolucio_seconds', 'Temps de resoluci\u00f3 per dia')
VIGILANTS_ACTIUS = Gauge('vvss_vigilants_actius', 'Nombre de vigilants actius')

# Actualitzar m\u00e8triques
start_http_server(8000)

# Exemple d'actualitzaci\u00f3
SERVEIS_COBERTS.set(90)
SERVEIS_DESCOBERTS.set(0)
TEMPS_RESOLUCIO.observe(0.093)
VIGILANTS_ACTIUS.set(15)
```

### **Scripts de Manteniment**

#### **Script de Netegesa de la Base de Dades**

```python
# cleanup_db.py
import sqlite3
from datetime import datetime, timedelta

def netejar_dades_antigues(dies=365):
    """Elimina dades m\u00e9s antigues de X dies."""
    conn = sqlite3.connect('vvss.db')
    cursor = conn.cursor()
    
    data_limite = (datetime.now() - timedelta(days=dies)).strftime('%Y-%m-%d')
    
    # Eliminar dades antigues del hist\u00f2ric
    cursor.execute("DELETE FROM historic_assignacions WHERE data_assignacio < ?", (data_limite,))
    cursor.execute("DELETE FROM historic_substitucions WHERE data_substitucio < ?", (data_limite,))
    cursor.execute("DELETE FROM descoberts WHERE data_registre < ?", (data_limite,))
    
    # VACUUM per a optimitzar
    cursor.execute("VACUUM;")
    
    conn.commit()
    conn.close()
    print(f"Dades anteriors a {data_limite} eliminades.")

if __name__ == "__main__":
    netejar_dades_antigues(dies=365)  # 1 any
```

#### **Script de Verificaci\u00f3 de Salut**

```python
# health_check.py
import sqlite3
import sys

def health_check():
    """Verifica l'estat de salut del sistema."""
    errors = []
    
    # 1. Verificar connexi\u00f3 a la base de dades
    try:
        conn = sqlite3.connect('vvss.db')
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
    except Exception as e:
        errors.append(f"Base de dades: {str(e)}")
    
    # 2. Verificar taules existents
    try:
        conn = sqlite3.connect('vvss.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        taules = [row[0] for row in cursor.fetchall()]
        taules_requerides = ['vigilants', 'serveis', 'assignacions', 'parametres_legals']
        for taula in taules_requerides:
            if taula not in taules:
                errors.append(f"Taula {taula} no trobada")
        conn.close()
    except Exception as e:
        errors.append(f"Verificaci\u00f3 de taules: {str(e)}")
    
    # 3. Verificar dades b\u00e0siques
    try:
        conn = sqlite3.connect('vvss.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM vigilants")
        if cursor.fetchone()[0] == 0:
            errors.append("No hi ha vigilants a la base de dades")
        cursor.execute("SELECT COUNT(*) FROM serveis")
        if cursor.fetchone()[0] == 0:
            errors.append("No hi ha serveis a la base de dades")
        conn.close()
    except Exception as e:
        errors.append(f"Verificaci\u00f3 de dades: {str(e)}")
    
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    else:
        print("\u2705 Sistema en estat de salut")
        sys.exit(0)

if __name__ == "__main__":
    health_check()
```

---

## \ud83d\udc80 **\u2699 Soluci\u00f3 de Problemres**

### **Problemres Comuns i Solucions**

#### **1. Error: "No module named 'ortools'"**

**Causa**: OR-Tools no est\u00e0 instal\u00b7lat.

**Soluci\u00f3**:
```bash
pip install ortools

# Si usas entorn virtual
source venv/bin/activate
pip install ortools
```

#### **2. Error: "sqlite3.OperationalError: unable to open database file"**

**Causa**: Permissos insuficients o cam\u00ed incorrecte.

**Soluci\u00f3**:
```bash
# Verificar permissos
ls -la vvss.db

# Donar permissos
chmod 664 vvss.db

# O crear la base de dades al directori actual
python -c "from database import reset_db; reset_db()"
```

#### **3. Error: "Model was not solved optimally"**

**Causa**: Temps l\u00edmit massa baix o problema massa complex.

**Soluci\u00f3**:
```python
# Augmentar temps l\u00edmit
solver.parameters.max_time_in_seconds = 60.0

# Augmentar treballadors
solver.parameters.num_workers = 16

# Reduir la mida del problema
# - Menys dies a planificar
# - Menys serveis
# - Menys restriccions
```

#### **4. Error: "Infeasible: No solution found"**

**Causa**: Restriccions massa estrictes o dades inconsistents.

**Soluci\u00f3**:
```python
# 1. Verificar dades d'entrada
from database import obtenir_vigilants, obtenir_serveis
vigilants = obtenir_vigilants()
serveis = obtenir_serveis()

# 2. Verificar restriccions
# - Assegurar que hi ha prou vigilants
# - Assegurar que les hores m\u00e0ximes s\u00f3n realistes
# - Assegurar que els binomis obligatoris tenen prou vigilants certificats

# 3. Relaxar restriccions (temporalment per a debug)
# - Reduir hores_max_setmana
# - Augmentar dies_max_consecutius
# - Desactivar binomi_obligatori
```

#### **5. Descoberts Excessius**

**Causa**: Falta de vigilants, restriccions massa estrictes, o dades mal configurades.

**Soluci\u00f3**:
```python
# 1. Augmentar el nombre de vigilants
# 2. Reduir el nombre de serveis
# 3. Verificar que els vigilants tenen les certificacions necess\u00e0ries
# 4. Augmentar hores_max_setmana (m\u00e0xim 48h per setmana)

# Exemple: Verificar certificacions
from database import obtenir_vigilants, obtenir_serveis

vigilants = obtenir_vigilants()
serveis_nit = [s for s in obtenir_serveis() if s.torn == 'nit' and s.binomi_obligatori]
vigilants_cctv = [v for v in vigilants if v.cert_cctv]

print(f"Serveis de nit amb binomi obligatori: {len(serveis_nit)}")
print(f"Vigilants amb CCTV: {len(vigilants_cctv)}")
print(f"Vigilants necessaris: {len(serveis_nit) * 2}")
```

#### **6. Temps de Resoluci\u00f3 Masses Llat**

**Causa**: Problema massa gran o configuraci\u00f3 sub\u00f2ptima.

**Soluci\u00f3**:
```python
# 1. Reduir la mida del problema
# - Menys dies a planificar
# - Menys serveis per dia

# 2. Optimitzar configuraci\u00f3 del solver
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_workers = 16
solver.parameters.cp_model_presolve = True

# 3. Usar Rolling Horizon amb finestres m\u00e9s petites
sistema = SistemaIntegrat(
    dies_finestra=3,      # Finestra m\u00e9s petita
    dies_lookback=1,
    dies_horitzo_total=7
)
```

#### **7. Error de Mem\u00f2ria**

**Causa**: Problema massa gran per a la mem\u00f2ria disponible.

**Soluci\u00f3**:
```bash
# 1. Augmentar mem\u00f2ria disponible
# - Usar un servidor amb m\u00e9s RAM
# - Tancar altres aplicacions

# 2. Reduir la mida del problema
# - Menys dies a planificar
# - Menys serveis

# 3. Usar Rolling Horizon
sistema = SistemaIntegrat(
    dies_finestra=3,
    dies_lookback=1,
    dies_horitzo_total=7
)
```

---

## \ud83d\udcbe **\u2699 Backup i Restauraci\u00f3**

### **Backup Manual**

```bash
# Crear backup de la base de dades
sqlite3 vvss.db ".backup vvss_backup_$(date +%Y%m%d_%H%M%S).db"

# Comprimir el backup
gzip vvss_backup_*.db

# Verificar el backup
sqlite3 vvss_backup_*.db "SELECT COUNT(*) FROM vigilants;"
```

### **Backup Autom\u00e0tic amb Cron**

```bash
# Editar crontab
crontab -e

# Afegir les següents l\u00ednies per a backup diari a les 2:00 AM
0 2 * * * /bin/bash -c 'sqlite3 /opt/vvss/vvss.db ".backup /var/backups/vvss/vvss_\$(date +\%Y\%m\%d_\%H\%M\%S).db"'

# O per a backup setmanal (diumenge a les 3:00 AM)
0 3 * * 0 /bin/bash -c 'sqlite3 /opt/vvss/vvss.db ".backup /var/backups/vvss/vvss_\$(date +\%Y\%m\%d).db"'
```

### **Restauraci\u00f3 de Backup**

```bash
# Restaurar des de backup
sqlite3 vvss.db ".restore vvss_backup.db"

# O amb Python
import shutil
shutil.copy2('vvss_backup.db', 'vvss.db')

# Verificar la restauraci\u00f3
python -c "from database import obtenir_vigilants; print(f'Vigilants: {len(obtenir_vigilants())}')"
```

### **Script de Backup Completa**

```python
# backup_system.py
import sqlite3
import shutil
import os
from datetime import datetime
import gzip

def crear_backup_complet(destinacio="./backups"):
    """Crea un backup complet del sistema."""
    os.makedirs(destinacio, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(destinacio, f"vvss_backup_{timestamp}")
    os.makedirs(backup_dir)
    
    # 1. Backup de la base de dades
    db_path = "vvss.db"
    backup_db_path = os.path.join(backup_dir, "vvss.db")
    if os.path.exists(db_path):
        shutil.copy2(db_path, backup_db_path)
    
    # 2. Backup dels fitxers de configuraci\u00f3
    config_files = ['requirements.txt', 'main.py', 'dades_exemple.py']
    for file in config_files:
        if os.path.exists(file):
            shutil.copy2(file, os.path.join(backup_dir, file))
    
    # 3. Comprimir el backup
    backup_zip = f"{backup_dir}.tar.gz"
    shutil.make_archive(backup_dir, 'gztar', backup_dir)
    
    # 4. Netejar directoris temporals
    shutil.rmtree(backup_dir)
    
    print(f"Backup creat: {backup_zip}")
    return backup_zip

def restaurar_backup(backup_path, destinacio="."):
    """Restaura un backup complet."""
    import tarfile
    
    # Extraure el backup
    with tarfile.open(backup_path, 'r:gz') as tar:
        tar.extractall(path=destinacio)
    
    # Obtenir el nom del directori del backup
    backup_dir = backup_path.replace('.tar.gz', '')
    
    # Restaurar la base de dades
    backup_db = os.path.join(backup_dir, "vvss.db")
    if os.path.exists(backup_db):
        shutil.copy2(backup_db, os.path.join(destinacio, "vvss.db"))
    
    print(f"Backup restaurat des de {backup_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restaurar_backup(sys.argv[2])
    else:
        crear_backup_complet()
```

---

## \ud83d\udd04 **\u2699 Actualitzacions**

### **Actualitzar el Codi**

```bash
# 1. Actualitzar des de GitHub
cd /opt/vvss
git pull origin main

# 2. Reiniciar el servei
sudo systemctl restart vvss

# 3. Verificar la versi\u00f3
python -c "import sys; sys.path.insert(0, '/opt/vvss'); from integrated_system import __version__; print(f'Versi\u00f3: {__version__}')"
```

### **Actualitzar Depend\u00e8ncies**

```bash
# 1. Actualitzar requirements.txt
cd /opt/vvss
pip install --upgrade -r requirements.txt

# 2. O actualitzar paquets individuals
/opt/vvss/venv/bin/pip install --upgrade ortools
/opt/vvss/venv/bin/pip install --upgrade pydantic
/opt/vvss/venv/bin/pip install --upgrade pandas

# 3. Reiniciar el servei
sudo systemctl restart vvss
```

### **Actualitzar Par\u00e0metres Legals**

```python
from database import actualitzar_parametres_legals

# Actualitzar amb nous par\u00e0metres
nous_parametres = {
    "descans_minim_hores": 13.0,
    "hores_max_setmana": 48,
    "dies_max_consecutius": 6,
}

actualitzar_parametres_legals(nous_parametres)
```

---

## \ud83d\udcc3 **\u2699 Resum de Comandes \u00daltiles**

| **Acci\u00f3** | **Comanda** | **Descripci\u00f3** |
|-------------|-------------|----------------|
| Iniciar servei | `sudo systemctl start vvss` | Inicia el servei VVSS |
| Aturar servei | `sudo systemctl stop vvss` | Atura el servei VVSS |
| Reiniciar servei | `sudo systemctl restart vvss` | Reinicia el servei |
| Veure estat | `sudo systemctl status vvss` | Mostra l'estat del servei |
| Veure logs | `sudo journalctl -u vvss -f` | Mostra logs en temps real |
| Backup | `sqlite3 vvss.db ".backup backup.db"` | Crea backup de la BD |
| Restaurar | `sqlite3 vvss.db ".restore backup.db"` | Restaura backup |
| Verificar salut | `python health_check.py` | Verifica l'estat del sistema |
| Netejar BD | `python cleanup_db.py` | Elimina dades antigues |

---

## \ud83c\udf01 **\u2699 Contacte i Suport**

### **Suport T\u00e8cnic**

- **GitHub Issues**: [https://github.com/fgcagents/vvss/issues](https://github.com/fgcagents/vvss/issues)
- **Correu electr\u00f2nic**: suport@fgcagents.cat
- **Documentaci\u00f3**: [README.md](./README.md)

### **Comunitat**

- **Discussions**: [GitHub Discussions](https://github.com/fgcagents/vvss/discussions)
- **Pull Requests**: [GitHub Pull Requests](https://github.com/fgcagents/vvss/pulls)

---

## \ud83c\udfc6 **\u2699 Agradeiments**

- **Google OR-Tools** per a la biblioteca d'optimitzaci\u00f3.
- **FGC (Ferrocarrils de la Generalitat de Catalunya)** pels requisits i el Pla de Seguretat.
- **Mossos d'Esquadra** per a la validaci\u00f3 legal.
- **Comunitat Open Source** per a les eines utilitzades.

---

> **\u26a0\ufe0f AV\u00cdS LEGAL**: Aquest sistema **compleix la normativa espanyola i catalana** en mat\u00e8ria de seguretat privada, jornada laboral i descans. No obstant aix\u00f2, **sempre consulteu amb el vostre assessor legal** abans d'implementar-lo en producci\u00f3.
