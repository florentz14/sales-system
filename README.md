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

## Librerías Python (`requirements.txt`)

Versiones pinnadas en **`requirements.txt`** (instalación: `pip install -r requirements.txt`). **Pydantic** (v2) llega como dependencia de **FastAPI**.

| Bloque | Paquetes (PyPI) |
|--------|-----------------|
| **API y servidor** | `fastapi`, `pydantic-settings`, `uvicorn[standard]` |
| **Base de datos y migraciones** | `SQLAlchemy`, `alembic`, `greenlet`, `psycopg[binary]` |
| **Colas y caché** | `celery`, `redis` |
| **Seguridad** | `bcrypt`, `python-jose[cryptography]`, `python-multipart` |
| **Análisis, estadística y gráficos** | `numpy`, `pandas`, `polars`, `pyarrow`, `scipy`, `statsmodels`, `matplotlib`, `seaborn` |
| **Informes y exportación** | `openpyxl`, `xlsxwriter`, `reportlab` |
| **Jupyter / notebooks** | `jupyterlab`, `notebook`, `ipykernel` |
| **CLI** | `tabulate` |
| **Tipado** | `typing_extensions` |

---

## Estructura del proyecto

```
sales_system/
├── app/
│   ├── main.py              # FastAPI
│   ├── api/v1/              # auth, products, customers, invoices, users, reports
│   ├── analytics/           # consultas, gráficos, export Excel/PDF
│   ├── cli/
│   │   ├── main.py          # entrada: python -m app.cli.main
│   │   └── menu.py          # menú interactivo (español)
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

En la raíz del proyecto hay **`.env.example`** (versionado). Cópialo a **`.env`** y ajusta valores:

```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

Al menos define un **`SECRET_KEY`** seguro en producción. El resto de variables está documentado en `.env.example`.

### 5. Base de datos

```bash
python -m alembic upgrade head
python scripts/seed.py
```

El *seed* es **idempotente** y rellena, entre otros:

- **Permisos** y **roles** (`admin`, `cashier`, `viewer`) alineados con `app.core.permissions`.
- **Usuarios demo** (misma contraseña que el nombre de usuario; cámbialos en producción): **`admin`**, **`cashier`**, **`viewer`**.
- **Perfiles** (`profiles`) para esos tres usuarios, con nombre para mostrar.
- **Clientes**: *Walk-in* y **Cliente demo (seed)**.
- **Proveedor**: **Proveedor central (seed)**.
- **Productos** con SKU `SEED-001` y `SEED-002`, **inventario** inicial y, si aún no existe, una **factura** demo sobre *Walk-in* (nota con texto de marcador *seed*, IVA 21 %).

### 6. Arrancar la API (opcional)

Si solo vas a usar el **menú de consola**, puedes omitir este paso. El CLI y la API comparten la misma base de datos (`DATABASE_URL`).

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Documentación interactiva: [http://localhost:8000/docs](http://localhost:8000/docs)
- Prefijo API: `/api/v1` (p. ej. login en `/api/v1/auth/login`)
- Punto de entrada del servidor: módulo **`app.main`**, variable **`app`** (archivo `app/main.py`).

### 7. Menú de consola

Después del paso 5 (migraciones + *seed*), ejecuta:

```bash
python -m app.cli.main
```

No hace falta tener Uvicorn en marcha. Detalle de opciones y comportamiento: sección **[Menú de consola (CLI)](#menú-de-consola-cli)**.

---

## Menú de consola (CLI)

Aplicación **interactiva en español** para gestionar el negocio desde la terminal. Usa la **misma base de datos** que la API (lee `DATABASE_URL` y el resto de ajustes desde `.env` vía `app.core.config`).

| Aspecto | Detalle |
|---------|---------|
| **Comando** | `python -m app.cli.main` |
| **Archivos** | Entrada: `app/cli/main.py` · Lógica: `app/cli/menu.py` · Tablas: `app/cli/tablefmt.py` · Consola: `app/cli/terminal.py` |
| **Salida tabular** | **tabulate** con formato propio (`CLI_TABLEFMT`): líneas `\|` y `-`, borde **superior e inferior**, sin `+` ni fila `=` bajo cabecera |
| **Auditoría** | Si hay **sesión CLI**, el actor es ese usuario; si no, el usuario **`admin`** si existe (*seed*) |
| **Validación** | Altas de usuario en consola pasan por **`app.utils.validation`** (Pydantic, alineado con `UserCreate`) |
| **Reportes en disco** | PNG, Excel y PDF se guardan en **`REPORTS_OUTPUT_DIR`** (por defecto `var/reports/`) |

**Importante:** el CLI **no usa JWT** ni la capa HTTP: abre sesiones SQLAlchemy directamente. **Login / registro** en consola actualizan la sesión en memoria del proceso (no emiten token). La **API REST** sigue siendo la vía adecuada para clientes externos, permisos por token y documentación OpenAPI.

### Menú principal

| Opción | Contenido |
|--------|-----------|
| **1** Productos | Listar, ver, crear, editar, eliminar (*soft delete*) |
| **2** Clientes | CRUD completo |
| **3** Facturas | Crear (líneas, descuento por línea, descuento global, IVA %), listar, ver, anular |
| **4** Inventario | Ver stock de todos los productos; fijar stock de un producto |
| **5** Proveedores | CRUD |
| **6** Reportes | KPIs y ventas diarias en tabla; rankings; gráficos PNG; exportación Excel/PDF |
| **7** Cuenta y sesión | Iniciar sesión (usuario/contraseña), cerrar sesión, ver usuario y permisos efectivos |
| **8** Registro | Si la base **no tiene usuarios**, crea el primer **admin**. Si ya hay usuarios, solo un usuario con **`manage_users`** puede dar de alta aquí |
| **9** Usuarios / RBAC | Listar usuarios; crear usuario; asignar roles; activar/desactivar; listar roles y permisos del sistema (las acciones de escritura exigen **`manage_users`** y sesión iniciada) |
| **10** Limpiar pantalla | Borra la consola (secuencias ANSI; consolas modernas) |
| **0** Salir | Cierra el programa |

Para salir en cualquier momento también puedes usar **Ctrl+C**.

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
