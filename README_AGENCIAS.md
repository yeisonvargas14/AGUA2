# Módulos de Agencias - Sistema de Purificadora

Este documento detalla la implementación, configuración y despliegue de los nuevos módulos desarrollados para la gestión de Agencias y el inicio de sesión por roles.

## Módulos Implementados

### 1. Inicios de Sesión por Roles (Módulo 1)
- **Botones específicos en Login:** Se agregaron botones de "Iniciar como Administrador" y "Iniciar como Agencia" en la página de login.
- **Validación de Roles:** Al hacer clic en cualquiera de estos botones, el sistema valida que el usuario pertenezca exactamente al rol seleccionado:
  - Administrador: Requiere ser superusuario o tener `role == 'admin'`.
  - Agencia: Requiere tener `role == 'agency'`.
  - Cliente/Repartidor: Inicio de sesión regular.
- **Redirección:** Después de un login exitoso, se redirige automáticamente al panel correspondiente (`rol_redirect`).
- **Bloqueo de Inactivos:** Si una agencia está inactiva (`activa = False`), no se le permite iniciar sesión y se le redirige al login mostrando un mensaje de error.

### 2. Gestión de Agencias (Módulo 2)
- **Panel de Administración (CRUD):** El administrador puede:
  - Listar agencias con estadísticas (pedidos totales, facturación total).
  - Detalle de agencia: Información de contacto, estadísticas visuales, mapa de ubicación y su historial de pedidos.
  - Crear agencias: Generación automática de contraseñas seguras y envío de correo con las credenciales.
  - Editar agencias (nombre de empresa, dirección, teléfono, coordenadas GPS, notas internas).
  - Activar/Desactivar agencias con un solo clic.
- **Panel de la Agencia:**
  - Panel principal (`/agencia/dashboard/`) con resumen de pedidos, estatus y mapa de entrega.
  - Crear pedidos específicos de agencia.
  - Cambio de contraseña seguro.

---

## Configuración y Variables de Entorno

### Configuración del Servidor de Correo (SMTP)
Para el envío de correos automatizados con las credenciales de las nuevas agencias en producción (Railway), se deben configurar las siguientes variables de entorno en el panel de Railway (o archivo `.env` local):

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com  # O tu proveedor SMTP
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_correo@gmail.com
EMAIL_HOST_PASSWORD=tu_contraseña_de_aplicacion
DEFAULT_FROM_EMAIL="Purificadora Agua <tu_correo@gmail.com>"
```

*Nota:* En desarrollo, si estas variables no están configuradas, los correos se imprimirán en la consola de Django. El proceso de creación de agencias no fallará gracias al uso de `fail_silently=True`.

---

## Despliegue en Railway

### 1. Aplicar Migraciones
Las migraciones ya están configuradas y listas. Al hacer push a Railway, el pipeline ejecutará automáticamente las migraciones o puedes ejecutarlas manualmente en la consola de Railway:
```bash
python backend/manage.py migrate
```

### 2. Actualización de Código
Para enviar los cambios al servidor en Railway, ejecute los siguientes comandos en su terminal local:
```bash
git add -A
git commit -m "feat: implementar botones de login por rol y CRUD completo de agencias"
git push origin main
```
Una vez que el build de Railway finalice con éxito, el sistema estará en línea con los nuevos módulos activos.
