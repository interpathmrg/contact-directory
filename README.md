# Directorio de Contactos Corporativo

Aplicación web empresarial para gestión de contactos corporativos con autenticación Azure Active Directory, importación/exportación masiva y generación de etiquetas de invitación en PDF.

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11 · FastAPI · SQLAlchemy async (asyncpg) |
| Frontend | React 18 · TypeScript · Tailwind CSS |
| Base de datos | PostgreSQL 15 |
| Migraciones | Alembic |
| Autenticación | Azure Active Directory (MSAL) + JWT |
| Contenedores | Docker · docker-compose |
| Proxy | Nginx |
| Tests | pytest · Jest |

---

## Módulos disponibles

| Módulo | Rol |
|---|---|
| Listado y CRUD de contactos | ADMIN + VIEWER |
| Importación masiva (Excel/CSV) | ADMIN |
| Exportación masiva (Excel/CSV) | ADMIN |
| Etiquetas de invitación PDF (Avery 5163) | ADMIN + VIEWER |
| Gestión de roles y accesos | ADMIN |

---

## Requisitos previos

- Docker Desktop ≥ 24.x con Docker Compose v2
- Una **App Registration en Azure AD** (ver sección de configuración)
- Node.js 20 (solo para desarrollo frontend local sin Docker)
- Python 3.11 (solo para desarrollo backend local sin Docker)

---

## 1 · Configuración de Azure AD

Antes de levantar el proyecto, configura una App Registration en Azure Portal:

1. Ve a **Azure Portal → Azure Active Directory → App registrations → New registration**
2. Nombre: `ContactDirectory` (o el que prefieras)
3. Supported account types: *Accounts in this organizational directory only*
4. Redirect URI: `Web` → agrega las URIs según tu entorno:
   - Docker local: `http://localhost/auth/callback`
   - K8s local: `https://contactos.local/auth/callback`
   - Producción: `https://tu-dominio.com/auth/callback`
5. Guarda el **Application (client) ID** y el **Directory (tenant) ID**
6. En **Certificates & secrets → New client secret** → copia el valor del secreto
7. En **API permissions** → agrega `User.Read` (Microsoft Graph, Delegated)
8. Haz clic en **Grant admin consent**

> **Nota:** El scope `User.Read` es suficiente. MSAL agrega `openid` y `profile` automáticamente — no los incluyas en la configuración.

---

## 2 · Setup local con Docker Compose

### 2.1 · Clonar y configurar variables de entorno

```bash
git clone <repo-url>
cd contact-directory

cp .env.example .env
```

Edita `.env` con tus valores reales:

```dotenv
# PostgreSQL
POSTGRES_USER=contactdb_user
POSTGRES_PASSWORD=MiPassword123!
POSTGRES_DB=contact_directory

# Seguridad
SECRET_KEY=cambia_esto_a_una_cadena_aleatoria_de_32_chars

# Azure AD
AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_SECRET=tu_client_secret_de_azure
AZURE_REDIRECT_URI=http://localhost/api/auth/callback

# Frontend
REACT_APP_API_URL=http://localhost/api
FRONTEND_URL=http://localhost
```

### 2.2 · Levantar los servicios

```bash
# Construir imágenes y levantar en background
docker compose up -d --build

# Ver logs en tiempo real
docker compose logs -f backend
```

Los servicios quedarán disponibles en:

| Servicio | URL |
|---|---|
| Aplicación | http://localhost |
| API Swagger | http://localhost/api/docs |
| Backend (directo) | http://localhost:8000 |

### 2.3 · Ejecutar las migraciones de base de datos

```bash
docker compose exec backend alembic upgrade head
```

Esto crea las tablas e inserta los datos semilla:
- **Sociedades:** EGE HAINA, SIBA, Trelia
- **Roles:** ADMIN, VIEWER

### 2.4 · Primer acceso

El primer usuario ADMIN debe insertarse directamente en la base de datos (no existe auto-asignación):

```bash
# Entrar a la consola de PostgreSQL
docker compose exec db sh -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB'
```

Dentro de psql:
```sql
INSERT INTO user_roles (id, user_email, role_id, assigned_by)
SELECT gen_random_uuid(), 'tu.email@empresa.com', r.id, 'system'
FROM roles r WHERE r.name = 'ADMIN';
\q
```

Luego:
1. Abre http://localhost
2. Haz clic en **Iniciar sesión con Microsoft**
3. Autentícate con la cuenta registrada como ADMIN

---

## 3 · Variables de entorno — referencia completa

| Variable | Requerida | Descripción |
|---|---|---|
| `POSTGRES_USER` | ✅ | Usuario de PostgreSQL |
| `POSTGRES_PASSWORD` | ✅ | Contraseña de PostgreSQL |
| `POSTGRES_DB` | ✅ | Nombre de la base de datos |
| `POSTGRES_HOST` | — | Host de PostgreSQL (default: `db`) |
| `POSTGRES_PORT` | — | Puerto de PostgreSQL (default: `5432`) |
| `SECRET_KEY` | ✅ | Clave secreta para firmar JWT (mín. 32 chars) |
| `JWT_ALGORITHM` | — | Algoritmo JWT (default: `HS256`) |
| `JWT_EXPIRE_MINUTES` | — | Tiempo de vida del access token (default: `60`) |
| `JWT_REFRESH_EXPIRE_DAYS` | — | Tiempo de vida del refresh token (default: `7`) |
| `AZURE_CLIENT_ID` | ✅ | Application ID de la App Registration |
| `AZURE_TENANT_ID` | ✅ | Directory ID del tenant de Azure AD |
| `AZURE_CLIENT_SECRET` | ✅ | Client secret de la App Registration |
| `AZURE_REDIRECT_URI` | ✅ | URI de redirección OAuth2 configurada en Azure |
| `ENVIRONMENT` | — | `development` o `production` (default: `development`) |
| `LOG_LEVEL` | — | Nivel de log (default: `INFO`) |
| `UPLOAD_MAX_SIZE_MB` | — | Tamaño máximo de archivos de importación (default: `10`) |
| `ALLOWED_ORIGINS` | — | Orígenes CORS separados por coma |
| `FRONTEND_URL` | — | URL base del frontend para redirecciones OAuth2 |

---

## 4 · Comandos útiles

```bash
# Ver estado de los servicios
docker compose ps

# Ejecutar migraciones
docker compose exec backend alembic upgrade head

# Revertir última migración
docker compose exec backend alembic downgrade -1

# Ver historial de migraciones
docker compose exec backend alembic history

# Crear nueva migración (tras modificar modelos)
docker compose exec backend alembic revision --autogenerate -m "descripcion_del_cambio"

# Acceder a la consola de PostgreSQL
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB

# Reiniciar solo el backend (tras cambios de código)
docker compose restart backend

# Ver logs del backend en tiempo real
docker compose logs -f backend

# Limpiar volúmenes (¡borra todos los datos!)
docker compose down -v
```

---

## 5 · Tests

### Backend (pytest)

```bash
# Dentro del contenedor
docker compose exec backend pytest

# Con coverage report
docker compose exec backend pytest --cov=app --cov-report=term-missing

# Archivo específico
docker compose exec backend pytest tests/test_auth.py -v

# Localmente (requiere Python 3.11 y dependencias instaladas)
cd backend
pip install -r requirements.txt
pytest
```

### Frontend (Jest)

```bash
# Dentro del contenedor (si el frontend está corriendo en dev mode)
docker compose exec frontend npm test -- --watchAll=false

# Localmente
cd frontend
npm install
npm test -- --watchAll=false
```

---

## 6 · Desarrollo local sin Docker

### Backend

```bash
cd backend

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp ../.env.example ../.env
# Editar .env con POSTGRES_HOST=localhost

# Iniciar servidor con hot-reload
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

npm install

# Las variables REACT_APP_* deben estar en .env o en el ambiente
REACT_APP_API_URL=http://localhost:8000/api npm start
```

---

## 7 · Arquitectura de servicios

```
                     Puerto 80 (host)
                           │
                     ┌─────┴─────┐
                     │   Nginx   │  (reverse proxy)
                     └─────┬─────┘
              ┌────────────┴────────────┐
              │                         │
    /api/* → backend:8000         /* → frontend:80
    /auth/* → backend:8000        (React SPA)
              │
     ┌────────┴────────┐
     │   FastAPI App   │
     │                 │
     │  /api/contacts  │
     │  /api/auth      │
     │  /api/import    │
     │  /api/export    │
     │  /api/labels    │
     │  /api/admin     │
     │  /health /ready │
     └────────┬────────┘
              │
        db:5432
     ┌────────┴────────┐
     │  PostgreSQL 15  │
     └─────────────────┘
```

### Flujo de autenticación

```
Usuario → [Login] → GET /api/auth/login → {auth_url}
       → Redirige a Microsoft
       → Microsoft → GET /api/auth/callback?code=xxx
       → Backend intercambia código por token Azure AD
       → Backend crea JWT propio
       → HTMLResponse → localStorage.setItem(tokens)
       → window.location = '/'
       → App lee JWT → usuario autenticado
```

---

## 8 · Despliegue en Kubernetes

### 8.1 · Requisitos previos del cluster

#### Storage provisioner (clusters kubeadm bare-metal)

Los clusters kubeadm no tienen StorageClass por defecto. Instala `local-path-provisioner` antes de desplegar:

```bash
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.28/deploy/local-path-storage.yaml
kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

Verifica: `kubectl get storageclass`

#### Ingress controller

Los manifests están configurados para **Traefik**. Verifica el nombre del entrypoint HTTP de tu instalación:

```bash
kubectl get deploy traefik -n traefik -o yaml | grep "entryPoints\."
```

Si Traefik tiene redirect HTTP→HTTPS (común), usa `websecure` en el IngressRoute (ya configurado en `k8s/ingress.yaml`).

### 8.2 · Build y push de imágenes

```bash
# Build de imágenes
docker build -t tu-usuario/contact-backend:latest ./backend
docker build -t tu-usuario/contact-frontend:latest ./frontend

# Push a Docker Hub (o tu registry)
docker push tu-usuario/contact-backend:latest
docker push tu-usuario/contact-frontend:latest
```

Actualiza las referencias de imagen en `k8s/deployment.yaml` con tu usuario.

### 8.3 · Generar el secret.yaml

```bash
# En Git Bash / Linux
echo -n "mi_valor" | base64

# En PowerShell
[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("mi_valor"))
```

Copia `k8s/secret.yaml.example` → `k8s/secret.yaml`, rellena los valores base64 y aplícalo. **No commitear `secret.yaml`** (está en `.gitignore`).

### 8.4 · Despliegue paso a paso

```bash
# 1. Namespace
kubectl apply -f k8s/namespace.yaml

# 2. Configuración
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# 3. Base de datos
kubectl apply -f k8s/postgres.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n contact-directory --timeout=90s

# 4. Aplicación
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/ingress.yaml

# 5. Migraciones (solo en el primer despliegue)
kubectl apply -f k8s/migration-job.yaml
kubectl wait --for=condition=complete job/alembic-migrate -n contact-directory --timeout=120s
kubectl logs -n contact-directory job/alembic-migrate
```

### 8.5 · Primer admin en K8s

```bash
kubectl exec -n contact-directory postgres-0 -- \
  psql -U contactdb_user -d contact_directory -c \
  "INSERT INTO user_roles (id, user_email, role_id, assigned_by)
   SELECT gen_random_uuid(), 'admin@empresa.com', r.id, 'system'
   FROM roles r WHERE r.name = 'ADMIN';"
```

### 8.6 · Configurar hostname

Obtén la IP del ingress controller (MetalLB):

```bash
kubectl get svc -n traefik
```

Agrega al `/etc/hosts` (Linux/Mac) o `C:\Windows\System32\drivers\etc\hosts` (Windows, como administrador):

```
<EXTERNAL-IP>  contactos.local
```

### 8.7 · Actualizar imagen tras cambios de código

A diferencia de Docker Compose, K8s no tiene hot-reload. Cada cambio requiere:

```bash
docker build -t tu-usuario/contact-backend:latest ./backend
docker push tu-usuario/contact-backend:latest
kubectl rollout restart deployment/backend -n contact-directory
kubectl rollout status deployment/backend -n contact-directory
```

### 8.8 · Mapeo de recursos

| Servicio | CPU Request | CPU Limit | Memory Request | Memory Limit |
|---|---|---|---|---|
| backend | 250m | 500m | 256Mi | 512Mi |
| frontend | 100m | 200m | 128Mi | 256Mi |
| postgres | 250m | 500m | 256Mi | 512Mi |

### 8.9 · Base de datos en producción

Para producción se recomienda usar PostgreSQL administrado:
- **Azure**: Azure Database for PostgreSQL Flexible Server
- **AWS**: Amazon RDS for PostgreSQL
- **GCP**: Cloud SQL for PostgreSQL

Solo cambia `POSTGRES_HOST` en el ConfigMap.

### 8.10 · Checklist antes de producción

- [ ] `SECRET_KEY` generada con `openssl rand -hex 32`
- [ ] `AZURE_REDIRECT_URI` usa `https://` y apunta al dominio de producción
- [ ] `ALLOWED_ORIGINS` y `FRONTEND_URL` usan `https://`
- [ ] URI registrada en Azure Portal
- [ ] `ENVIRONMENT=production` (desactiva Swagger docs)
- [ ] `LOG_LEVEL=WARNING`
- [ ] Certificado TLS real configurado (cert-manager + Let's Encrypt)
- [ ] Backup automático de PostgreSQL configurado
- [ ] HorizontalPodAutoscaler para backend (≥ 2 réplicas)

---

## 9 · Estructura del proyecto

```
contact-directory/
├── docker-compose.yml          # Entorno de desarrollo
├── docker-compose.prod.yml     # Override de producción
├── .env.example                # Plantilla de variables de entorno
├── .gitignore
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py              # Migraciones async
│   │   └── versions/
│   │       └── 0001_initial_schema.py
│   ├── app/
│   │   ├── main.py             # Entry point FastAPI
│   │   ├── config.py           # Settings (pydantic-settings)
│   │   ├── database.py         # Async engine y session
│   │   ├── models/             # SQLAlchemy ORM
│   │   │   ├── contact.py
│   │   │   ├── society.py
│   │   │   ├── role.py
│   │   │   └── user_role.py
│   │   ├── schemas/            # Pydantic (request/response)
│   │   │   ├── auth.py
│   │   │   ├── contact.py
│   │   │   ├── society.py
│   │   │   ├── import_export.py
│   │   │   ├── labels.py
│   │   │   └── admin.py
│   │   ├── routers/            # FastAPI routers
│   │   │   ├── auth.py
│   │   │   ├── contacts.py
│   │   │   ├── import_export.py
│   │   │   ├── labels.py
│   │   │   └── admin.py
│   │   ├── services/           # Lógica de negocio
│   │   │   ├── contact_service.py
│   │   │   ├── import_service.py
│   │   │   ├── label_service.py
│   │   │   └── admin_service.py
│   │   ├── auth/
│   │   │   ├── azure.py        # MSAL integration
│   │   │   └── dependencies.py # JWT + FastAPI deps
│   │   └── utils/
│   │       ├── excel_handler.py  # openpyxl
│   │       └── pdf_generator.py  # reportlab (Avery 5163)
│   └── tests/
│       ├── conftest.py
│       ├── test_health.py
│       ├── test_auth.py
│       ├── test_excel.py
│       ├── test_import_validation.py
│       └── test_contacts.py
│
├── frontend/
│   ├── Dockerfile              # Multi-stage: Node build → Nginx
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── nginx.conf              # SPA config
│   ├── public/index.html
│   └── src/
│       ├── App.tsx
│       ├── index.tsx
│       ├── index.css           # Tailwind + custom classes
│       ├── setupTests.ts
│       ├── types/index.ts      # TypeScript types
│       ├── services/           # Axios API clients
│       │   ├── api.ts
│       │   ├── authService.ts
│       │   └── contactService.ts
│       ├── hooks/
│       │   └── useAuth.tsx     # AuthContext + hook
│       ├── components/
│       │   ├── auth/ProtectedRoute.tsx
│       │   └── common/
│       │       ├── Layout.tsx
│       │       ├── Navbar.tsx
│       │       ├── LoadingSpinner.tsx
│       │       ├── Pagination.tsx
│       │       └── ConfirmDialog.tsx
│       ├── pages/
│       │   ├── LoginPage.tsx
│       │   ├── ContactsPage.tsx
│       │   ├── ContactFormPage.tsx
│       │   ├── LabelsPage.tsx
│       │   ├── ImportPage.tsx
│       │   └── AdminPage.tsx
│       └── __tests__/
│           ├── LoadingSpinner.test.tsx
│           └── Pagination.test.tsx
│
├── nginx/
│   └── nginx.conf              # Reverse proxy principal
│
└── k8s/                        # Manifests de referencia
    ├── deployment.yaml
    ├── service.yaml
    ├── configmap.yaml
    └── secret.yaml.example
```

---

## 10 · API — Endpoints principales

Base URL: `http://localhost/api`

### Autenticación
```
GET  /auth/login              → URL de Microsoft login
GET  /auth/callback           → OAuth2 callback (uso interno del navegador)
POST /auth/refresh            → Renovar access token
GET  /auth/me                 → Info del usuario actual
POST /auth/logout             → Cerrar sesión
```

### Contactos
```
GET    /contacts              → Listar (paginación, búsqueda, filtros)
GET    /contacts/{id}         → Obtener por ID
POST   /contacts              → Crear [ADMIN]
PUT    /contacts/{id}         → Actualizar [ADMIN]
DELETE /contacts/{id}         → Soft delete [ADMIN]
GET    /contacts/societies/all → Lista de sociedades (dropdown)
```

### Importación / Exportación
```
GET  /import/template         → Descargar plantilla Excel [ADMIN]
POST /import/preview          → Preview del archivo subido [ADMIN]
POST /import/confirm          → Confirmar importación [ADMIN]
GET  /export/preview          → Resumen de exportación [ADMIN]
GET  /export/download         → Descargar Excel/CSV [ADMIN]
```

### Etiquetas
```
POST /labels/preview          → Vista previa de contactos [ADMIN+VIEWER]
POST /labels/pdf              → Generar PDF Avery 5163 [ADMIN+VIEWER]
```

### Administración
```
GET    /admin/roles           → Lista de roles [ADMIN]
GET    /admin/users           → Lista de usuarios con acceso [ADMIN]
POST   /admin/users           → Asignar acceso por email [ADMIN]
PUT    /admin/users/{id}/role → Cambiar rol [ADMIN]
DELETE /admin/users/{id}      → Revocar acceso [ADMIN]
```

### Operaciones
```
GET /health    → Liveness probe
GET /ready     → Readiness probe (verifica BD)
```

Documentación interactiva disponible en http://localhost/api/docs (solo en `ENVIRONMENT=development`).

---

## 11 · Solución de problemas frecuentes

**El backend no arranca y dice "could not connect to server"**
```bash
# Espera a que PostgreSQL esté listo
docker compose logs db
# Si el healthcheck no pasa, revisa las credenciales en .env
```

**Error "Token inválido o expirado" al hacer peticiones**
```bash
# El SECRET_KEY cambió o el token expiró
# Cierra sesión en la app y vuelve a autenticarte
```

**La migración falla con "relation already exists"**
```bash
# La BD ya tiene datos de una versión anterior
docker compose exec backend alembic current
docker compose exec backend alembic heads
# Si es necesario, resetear (¡pierde datos!):
docker compose down -v && docker compose up -d
docker compose exec backend alembic upgrade head
```

**El primer usuario no se auto-asigna como ADMIN**
```bash
# Verificar que no exista ningún admin previo
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB \
  -c "SELECT ur.user_email, r.name FROM user_roles ur JOIN roles r ON r.id = ur.role_id;"
```

**Error de CORS en el navegador**
```bash
# Verificar que ALLOWED_ORIGINS en .env incluye el origen del navegador
ALLOWED_ORIGINS=http://localhost,http://localhost:3000
```

---

## Licencia

Uso interno corporativo. Todos los derechos reservados.
