# Sales System

Backend de **gestión de ventas** con API REST (FastAPI), menú CLI, RBAC, facturación (IVA y descuentos), inventario y **reportes** (JSON, gráficos PNG, Excel y PDF).

**Repositorio:** [github.com/florentz14/sales-system](https://github.com/florentz14/sales-system) · Licencia **MIT** (ver `LICENSE`).

---

## Características

| Área | Detalle |
|------|---------|
| **API** | Productos, clientes, facturas, usuarios; autenticación JWT |
| **RBAC** | Roles `admin`, `cashier`, `viewer` y permisos granulares |
| **Facturas** | Líneas con descuento %, descuento global, tipo impositivo, numeración `INV-xxxxxxxx` |
| **Datos** | Auditoría y *soft delete* en entidades principales |
| **CLI** | Menú en español (CRUD + reportes y exportación a `var/reports/`) |
| **Analytics** | Resumen de ventas, rankings; Matplotlib/Seaborn; export OpenPyXL y ReportLab |

---

## Stack

- **Python** 3.11+
- **FastAPI**, **Pydantic**, **Uvicorn**
- **SQLAlchemy 2** + **Alembic** (SQLite por defecto; PostgreSQL vía `DATABASE_URL`)
- **JWT** (access token), contraseñas con **bcrypt**
- **Pandas**, **Matplotlib**, **Seaborn**, **OpenPyXL**, **ReportLab**
- **Docker Compose**: API, PostgreSQL, Redis, worker **Celery** (opcional según despliegue)

---

## Estructura del proyecto

```
sales_system/
├── app/
│   ├── main.py              # FastAPI
│   ├── api/v1/              # auth, products, customers, invoices, users, reports
│   ├── analytics/           # consultas, gráficos, export Excel/PDF
│   ├── cli/                 # menú interactivo
│   ├── core/                # config, security, permissions
│   ├── db/models/           # ORM
│   ├── schemas/
│   ├── services/
│   └── utils/audit.py
├── alembic/versions/        # migraciones
├── scripts/seed.py          # RBAC + usuario admin + cliente demo
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── var/reports/             # salida de reportes CLI (gitignored salvo .gitkeep)
```

---

## Instalación local

### 1. Clonar

```bash
git clone https://github.com/florentz14/sales-system.git
cd sales-system
```

### 2. Entorno virtual

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate
```

### 3. Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configuración

Crea `.env` en la raíz (opcional). Ejemplo:

```env
DATABASE_URL=sqlite:///./sales.db
SECRET_KEY=cambia-esto-en-produccion
```

### 5. Base de datos

```bash
python -m alembic upgrade head
python scripts/seed.py
```

El *seed* crea permisos, roles, usuario **`admin`** / contraseña **`admin`** (cámbiala en producción) y el cliente *Walk-in*.

### 6. Arrancar la API

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Documentación interactiva: [http://localhost:8000/docs](http://localhost:8000/docs)
- Prefijo API: `/api/v1` (p. ej. login en `/api/v1/auth/login`)

### 7. Menú CLI

```bash
python -m app.cli.main
```

---

## Autenticación

`POST /api/v1/auth/login` (formulario OAuth2: `username`, `password`).

Respuesta: `{"access_token": "...", "token_type": "bearer"}`.

Incluye el token en cabecera: `Authorization: Bearer <token>`.

---

## Reportes (API)

Requiere permiso **`read_report`** (incluido en *seed* para roles adecuados).

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/reports/summary` | JSON: KPIs, ventas diarias, top productos y clientes |
| GET | `/api/v1/reports/chart/sales` | PNG: ventas por día |
| GET | `/api/v1/reports/chart/products` | PNG: top productos |
| GET | `/api/v1/reports/export/excel` | Descarga `.xlsx` |
| GET | `/api/v1/reports/export/pdf` | Descarga `.pdf` |

Query comunes: `days` (por defecto 30), `start_date`, `end_date`, `ranking_limit`.

---

## Docker

```bash
docker compose up --build
```

Define `DATABASE_URL` para PostgreSQL dentro de la red del compose. Aplica migraciones y *seed* según tu flujo de despliegue.

---

## Permisos (ejemplos)

Definidos en `app/core/permissions.py`, por ejemplo: `create_product`, `read_invoice`, `read_report`, `manage_users`, etc.

---

## Roadmap / ideas

- Tests automatizados y CI (GitHub Actions)
- Refresh tokens y endurecimiento de seguridad
- Frontend (dashboard)
- Rate limiting en endpoints sensibles
- Multi-tenant (si aplica)

---

## Contribuciones

*Fork* y *pull requests* son bienvenidos. Para cambios grandes, abre antes una *issue* para alinear el diseño.

---

## Autor

Proyecto de aprendizaje y base para ERP/POS; evolución documentada en el propio código y en este README.
