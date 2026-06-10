# Documentación del Flujo de Pedidos (AquaFlow)

Esta guía explica la configuración, estructura y flujo del sistema de pedidos y carritos de compra implementado en el proyecto.

## 1. Características Principales
- **Carrito Anónimo**: Los usuarios pueden agregar productos a su carrito sin iniciar sesión. Se almacena usando `request.session.session_key` de Django.
- **Fusión de Carrito**: Al iniciar sesión o registrarse, el contenido del carrito anónimo se transfiere automáticamente a la cuenta del usuario.
- **Validación de Ubicación**: En el Paso 1 del Checkout, se valida mediante Google Maps API y Ray Casting que el cliente esté dentro del casco urbano de Comarapa.
- **Checkout en 2 Pasos**:
  - **Paso 1**: Confirmar dirección de entrega detallada, instrucciones especiales y ubicación en el mapa.
  - **Paso 2**: Forzar registro/login (por número de celular) solo si es la primera vez que se realiza un pedido. Si ya está autenticado, se crea directamente.
- **Historial de Estados (`OrderLog`)**: Registro histórico detallado de transiciones de estado (ej: pendiente -> aceptado -> en camino -> entregado).
- **Notificaciones Pusher en Tiempo Real**: Notificaciones inmediatas en los paneles de administración y repartidores al crearse un pedido, con actualización dinámica de tablas sin recargar.

## 2. Configuración Requerida (.env)
Asegúrese de configurar las siguientes variables en el archivo `.env` o en Railway:
```env
PUSHER_APP_ID=1987654
PUSHER_KEY=a1b2c3d4e5f6g7h8i9j0
PUSHER_SECRET=s1e2c3r4e5t6
PUSHER_CLUSTER=mt1
GOOGLE_MAPS_API_KEY=su_clave_api_aqui
```

## 3. Instrucciones de Prueba

### Flujo del Cliente
1. Ingrese a la Landing Page de forma anónima.
2. Agregue productos al carrito (se mostrará un Toast verde gracias a la llamada AJAX, y el badge del navbar se actualizará automáticamente).
3. Diríjase al Carrito y presione "Proceder al Pago".
4. En el Paso 1 de Checkout, complete la dirección y marque su ubicación en el mapa de Comarapa (debe estar dentro del polígono para habilitar el botón de continuar).
5. En el Paso 2 de Checkout, complete el formulario de Registro (pestaña Registrarse) usando un número de celular único.
6. Al finalizar, será redirigido a la página de éxito de pedido y su sesión permanecerá iniciada.

### Flujo del Administrador / Repartidor
1. Inicie sesión en `/login/` como administrador o repartidor.
2. Abra la lista de pedidos pendientes.
3. Al realizar un pedido como cliente de forma paralela, verá aparecer un Toast flotante y una nueva fila resaltada en celeste en la tabla en tiempo real.
4. El administrador puede asignar un repartidor, lo cual cambiará el estado a Aceptado y registrará la acción en el log.
5. El repartidor asignado verá el pedido en su panel y podrá actualizar su estado a "En camino" y finalmente "Entregado", registrando las notas correspondientes.
6. En la consola del servidor de desarrollo se imprimirán logs simulados de notificaciones de WhatsApp enviadas al cliente.
