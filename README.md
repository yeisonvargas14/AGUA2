# 💧 Agua de Mesa Santiago — Sistema de Gestión de Purificadora de Agua

Sistema completo de gestión y distribución de agua purificada para el municipio de Comarapa, Santa Cruz, Bolivia. Permite la gestión de pedidos, entregas, inventario, cupones, promociones y valoraciones con roles diferenciados para administradores, agencias, repartidores y clientes.

---

## 📋 Tabla de Contenidos

- [Requisitos del Sistema](#requisitos-del-sistema)
- [Configuración del Entorno Virtual](#configuración-del-entorno-virtual)
- [Instalación de Dependencias](#instalación-de-dependencias)
- [Variables de Entorno](#variables-de-entorno)
- [Aplicar Migraciones](#aplicar-migraciones)
- [Ejecutar el Servidor](#ejecutar-el-servidor)
- [Roles y Usuarios](#roles-y-usuarios)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Endpoints de la API](#endpoints-de-la-api)

---

## ✅ Requisitos del Sistema

- **Python** 3.11 o superior
- **PostgreSQL** 14+ (base de datos principal en Railway)
- **pip** actualizado
- Conexión a Internet (para Railway DB y librerías externas)

---

## 🐍 Configuración del Entorno Virtual

```bash
# Crear el entorno virtual
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en Linux/macOS
source venv/bin/activate
```

---

## 📦 Instalación de Dependencias

```bash
pip install -r requirements.txt
```

Librerías principales incluidas:
| Librería | Versión | Uso |
|---|---|---|
| Django | >=5.0,<6.1 | Framework principal |
| djangorestframework | >=3.14.0 | Endpoints API REST |
| psycopg2-binary | >=2.9.0 | Conector PostgreSQL |
| pusher | >=3.3.0 | Notificaciones en tiempo real |
| Pillow | >=10.0.0 | Manejo de imágenes (avatares, productos) |
| dj-database-url | >=2.1.0 | Configuración de DB via URL |
| whitenoise | >=6.6.0 | Servir archivos estáticos en producción |
| django-widget-tweaks | >=1.5.0 | Personalización de formularios Django |
| gunicorn | >=21.2.0 | Servidor WSGI para producción |

---

## 🔐 Variables de Entorno

Copia el archivo de ejemplo y rellena los valores:

```bash
cp .env.example .env
```

Edita `.env` con tus valores reales:

```ini
# Django core
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=*

# PostgreSQL (Railway o local)
DATABASE_URL=postgresql://usuario:contraseña@host:puerto/nombre_db

# Pusher (notificaciones en tiempo real para repartidores)
PUSHER_APP_ID=tu-app-id
PUSHER_KEY=tu-key
PUSHER_SECRET=tu-secret
PUSHER_CLUSTER=mt1

# Google Maps (geolocalización de entregas)
GOOGLE_MAPS_API_KEY=tu-api-key

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-contrasena-de-aplicacion
```

> **Nota**: El archivo `.env` **nunca** debe subirse al repositorio Git. Está listado en `.gitignore`.

---

## 🗄️ Aplicar Migraciones

```bash
python backend/manage.py migrate
```

Para poblar la base de datos con datos de prueba automáticamente, visita:
```
http://127.0.0.1:8000/api/seed/
```

O crea un superusuario manualmente:
```bash
python backend/manage.py createsuperuser
```

---

## 🚀 Ejecutar el Servidor de Desarrollo

```bash
python backend/manage.py runserver
```

La aplicación estará disponible en: **http://127.0.0.1:8000/**

---

## 👥 Roles y Usuarios

El sistema tiene cuatro roles principales. Al iniciar sesión, cada usuario es redirigido automáticamente a su panel correspondiente:

| Rol | Panel | Ruta |
|---|---|---|
| **Administrador** | Gestión completa del sistema | `/administrador/` |
| **Agencia** | Registro de ventas y pedidos locales | `/agencia/` |
| **Repartidor** | Asignación y entrega de pedidos | `/repartidor/` |
| **Cliente** | Catálogo, carrito, historial de pedidos | `/catalogo/` |

La **pantalla de inicio pública** (`/`) es visible para cualquier visitante sin necesidad de iniciar sesión.

---

## 🗂️ Estructura del Proyecto

```
infor/
├── backend/
│   ├── manage.py
│   ├── purificadora/        # Configuración principal (settings, urls)
│   ├── accounts/            # Usuarios, autenticación, roles
│   ├── products/            # Catálogo de productos
│   ├── orders/              # Carrito, pedidos, checkout
│   ├── agencies/            # Panel de sucursales
│   ├── distribution/        # Panel de repartidores / entregas
│   ├── inventory/           # Historial de movimientos de stock
│   ├── notifications/       # Notificaciones internas
│   ├── coupons/             # Cupones de descuento personales
│   ├── promotions/          # Promociones globales por fecha
│   ├── ratings/             # Valoraciones de repartidores y productos
│   └── core/                # Vistas de admin + API REST del Dashboard
│
├── frontend/
│   ├── templates/
│   │   ├── base.html        # Plantilla base con sidebar por rol
│   │   ├── landing.html     # Pantalla de inicio pública
│   │   ├── auth/            # Login, registro, recuperación de contraseña
│   │   ├── admin_panel/     # Vistas del administrador
│   │   ├── client/          # Catálogo, carrito, pedidos, valoración
│   │   ├── agency/          # Dashboard de agencia
│   │   └── driver/          # Dashboard de repartidor
│   └── static/
│       ├── css/styles.css   # Sistema de diseño premium
│       └── js/
│           ├── app.js       # Dashboard SPA interactivo
│           └── maps.js      # Integración de Google Maps
│
├── requirements.txt
├── .env.example
├── Procfile                 # Para despliegue en Railway/Heroku
└── runtime.txt
```

---

## 🔌 Endpoints de la API

Estos endpoints son utilizados por el Dashboard SPA (`app.js`) y no requieren autenticación JWT (son de uso interno del dashboard administrativo):

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/seed/` | Poblar DB con datos de demostración |
| `GET` | `/api/stats/` | Estadísticas del Dashboard |
| `GET/POST` | `/api/products/` | Listar y crear productos |
| `PUT/DELETE` | `/api/products/<id>/` | Editar o eliminar un producto |
| `GET/POST` | `/api/orders/` | Listar y crear pedidos |
| `PUT` | `/api/orders/<id>/status/` | Cambiar estado de un pedido |
| `GET` | `/api/agencies/` | Listar sucursales/agencias |
| `GET` | `/api/inventory/` | Historial de movimientos de stock |
| `GET` | `/api/deliveries/` | Estado de las entregas activas |

---

## 🧪 Ejecutar Pruebas Unitarias

```bash
python backend/manage.py test --verbosity=2
```

---

## 🌐 Despliegue en Producción (Railway)

El proyecto ya está configurado para Railway:
1. Conecta tu repositorio en [railway.app](https://railway.app)
2. Agrega las variables de entorno en el panel de Railway
3. El `Procfile` ya incluye el comando de inicio con `gunicorn`
4. La base de datos PostgreSQL de Railway ya está configurada en `settings.py`
