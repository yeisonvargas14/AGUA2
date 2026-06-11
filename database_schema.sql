-- ============================================================
--  AQUAFLOW — Esquema completo de base de datos PostgreSQL
--  Generado desde los modelos Django del proyecto
--  Actualizado: 2026-06-10
-- ============================================================


-- ============================================================
--  0. DJANGO SYSTEM TABLES (auth_group, auth_permission, django_content_type)
--     Requeridas para las relaciones de permisos y grupos.
-- ============================================================
CREATE TABLE IF NOT EXISTS django_content_type (
    id                  SERIAL PRIMARY KEY,
    app_label           VARCHAR(100)            NOT NULL,
    model               VARCHAR(100)            NOT NULL,
    UNIQUE (app_label, model)
);

CREATE TABLE IF NOT EXISTS auth_permission (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(255)            NOT NULL,
    content_type_id     INTEGER                 NOT NULL REFERENCES django_content_type(id) ON DELETE CASCADE,
    codename            VARCHAR(100)            NOT NULL,
    UNIQUE (content_type_id, codename)
);

CREATE TABLE IF NOT EXISTS auth_group (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(150)            NOT NULL UNIQUE
);


-- ============================================================
--  1. USUARIOS (accounts.User)
--     Extiende AbstractUser de Django.
--     USERNAME_FIELD = 'telefono' (no username ni email)
-- ============================================================
CREATE TABLE IF NOT EXISTS accounts_user (
    id                  SERIAL PRIMARY KEY,
    -- Django AbstractUser base fields
    password            VARCHAR(128)            NOT NULL,
    last_login          TIMESTAMP WITH TIME ZONE,
    is_superuser        BOOLEAN                 NOT NULL DEFAULT FALSE,
    is_staff            BOOLEAN                 NOT NULL DEFAULT FALSE,
    is_active           BOOLEAN                 NOT NULL DEFAULT TRUE,
    date_joined         TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    first_name          VARCHAR(150)            NOT NULL DEFAULT '',
    last_name           VARCHAR(150)            NOT NULL DEFAULT '',
    -- Campos personalizados
    username            VARCHAR(150)            UNIQUE,          -- Opcional (puede ser NULL)
    email               VARCHAR(254)            UNIQUE,          -- Opcional (puede ser NULL)
    telefono            VARCHAR(20)             UNIQUE,          -- Identificador principal de login
    role                VARCHAR(15)             NOT NULL DEFAULT 'client',
        -- Valores: 'admin' | 'vendedor' | 'agency' | 'client' | 'driver'
    address             VARCHAR(255)            NOT NULL DEFAULT '',
    municipio           VARCHAR(100)            NOT NULL DEFAULT '',
    avatar              VARCHAR(100)            -- Ruta del archivo: avatars/<nombre>
);

-- Tabla intermedia Django para permisos de usuario
CREATE TABLE IF NOT EXISTS accounts_user_groups (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES accounts_user(id) ON DELETE CASCADE,
    group_id    INTEGER NOT NULL REFERENCES auth_group(id)    ON DELETE CASCADE,
    UNIQUE (user_id, group_id)
);

CREATE TABLE IF NOT EXISTS accounts_user_user_permissions (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES accounts_user(id)       ON DELETE CASCADE,
    permission_id   INTEGER NOT NULL REFERENCES auth_permission(id)     ON DELETE CASCADE,
    UNIQUE (user_id, permission_id)
);


-- ============================================================
--  2. CÓDIGOS DE RECUPERACIÓN DE CONTRASEÑA
--     (accounts.PasswordResetCode)
-- ============================================================
CREATE TABLE IF NOT EXISTS accounts_passwordresetcode (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER         NOT NULL REFERENCES accounts_user(id) ON DELETE CASCADE,
    telefono    VARCHAR(20)     NOT NULL,
    codigo      VARCHAR(6)      NOT NULL,
    creado_en   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expira_en   TIMESTAMP WITH TIME ZONE NOT NULL,
    usado       BOOLEAN         NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_reset_code_telefono_codigo
    ON accounts_passwordresetcode (telefono, codigo);


-- ============================================================
--  3. PERFIL DE REPARTIDOR (accounts.DriverProfile)
-- ============================================================
CREATE TABLE IF NOT EXISTS accounts_driverprofile (
    id                  SERIAL PRIMARY KEY,
    user_id             INTEGER         NOT NULL UNIQUE REFERENCES accounts_user(id) ON DELETE CASCADE,
    vehicle             VARCHAR(20)     NOT NULL DEFAULT 'moto',
        -- Valores: 'moto' | 'auto' | 'bicicleta'
    phone               VARCHAR(20)     NOT NULL DEFAULT '',
    active              BOOLEAN         NOT NULL DEFAULT TRUE,
    rating_avg          FLOAT           NOT NULL DEFAULT 0.0,
    current_latitude    DECIMAL(10, 6),
    current_longitude   DECIMAL(10, 6)
);


-- ============================================================
--  4. CATEGORÍAS DE PRODUCTOS (products.Category)
-- ============================================================
CREATE TABLE IF NOT EXISTS products_category (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100)    NOT NULL UNIQUE,
    description TEXT            NOT NULL DEFAULT ''
);


-- ============================================================
--  5. PRODUCTOS (products.Product)
-- ============================================================
CREATE TABLE IF NOT EXISTS products_product (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100)    NOT NULL,
    description TEXT            NOT NULL DEFAULT '',
    price       DECIMAL(10, 2)  NOT NULL,
    stock       INTEGER         NOT NULL DEFAULT 0 CHECK (stock >= 0),
    image       VARCHAR(100),   -- Ruta relativa: products/<nombre_archivo>
    is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    category_id INTEGER         REFERENCES products_category(id) ON DELETE SET NULL
);


-- ============================================================
--  6. AGENCIAS / SUCURSALES (agencies.Agency)
-- ============================================================
CREATE TABLE IF NOT EXISTS agencies_agency (
    id              SERIAL PRIMARY KEY,
    usuario_id      INTEGER         NOT NULL UNIQUE REFERENCES accounts_user(id) ON DELETE CASCADE,
    nombre_empresa  VARCHAR(200)    NOT NULL DEFAULT '',
    direccion       TEXT            NOT NULL DEFAULT '',
    telefono        VARCHAR(20)     NOT NULL DEFAULT '',
    email_contacto  VARCHAR(254)    NOT NULL DEFAULT '',
    fecha_creacion  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    activa          BOOLEAN         NOT NULL DEFAULT TRUE,
    notas_internas  TEXT            NOT NULL DEFAULT '',
    logo            VARCHAR(100),   -- Ruta relativa: logos/<nombre_archivo>
    latitud         DECIMAL(9, 6),
    longitud        DECIMAL(9, 6)
);


-- ============================================================
--  7. CUPONES DE DESCUENTO (coupons.Coupon)
-- ============================================================
CREATE TABLE IF NOT EXISTS coupons_coupon (
    id                  SERIAL PRIMARY KEY,
    code                VARCHAR(20)     NOT NULL UNIQUE,
    user_client_id      INTEGER         NOT NULL REFERENCES accounts_user(id) ON DELETE CASCADE,
    discount_percentage INTEGER         NOT NULL CHECK (discount_percentage > 0 AND discount_percentage <= 100),
    expires_at          TIMESTAMP WITH TIME ZONE NOT NULL,
    used                BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);


-- ============================================================
--  8. PROMOCIONES (promotions.Promotion)
-- ============================================================
CREATE TABLE IF NOT EXISTS promotions_promotion (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(100)    NOT NULL,
    description         TEXT            NOT NULL DEFAULT '',
    discount_percentage INTEGER         NOT NULL CHECK (discount_percentage > 0),
    start_date          TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date            TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active           BOOLEAN         NOT NULL DEFAULT TRUE
);

-- Tabla intermedia M2M: Promoción ↔ Producto
CREATE TABLE IF NOT EXISTS promotions_promotion_products (
    id              SERIAL PRIMARY KEY,
    promotion_id    INTEGER NOT NULL REFERENCES promotions_promotion(id) ON DELETE CASCADE,
    product_id      INTEGER NOT NULL REFERENCES products_product(id)    ON DELETE CASCADE,
    UNIQUE (promotion_id, product_id)
);


-- ============================================================
--  9. CARRITO DE COMPRAS (orders.Cart)
--     Soporta carrito anónimo (session_key) y autenticado (user)
-- ============================================================
CREATE TABLE IF NOT EXISTS orders_cart (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER         REFERENCES accounts_user(id) ON DELETE CASCADE,
    session_key VARCHAR(40)     UNIQUE,  -- Clave de sesión para carritos anónimos
    created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cart_session_key ON orders_cart (session_key);


-- ============================================================
--  10. ÍTEMS DEL CARRITO (orders.CartItem)
-- ============================================================
CREATE TABLE IF NOT EXISTS orders_cartitem (
    id              SERIAL PRIMARY KEY,
    cart_id         INTEGER         NOT NULL REFERENCES orders_cart(id)       ON DELETE CASCADE,
    product_id      INTEGER         NOT NULL REFERENCES products_product(id)  ON DELETE CASCADE,
    quantity        INTEGER         NOT NULL DEFAULT 1 CHECK (quantity > 0),
    price_at_time   DECIMAL(10, 2)  NOT NULL DEFAULT 0,
    price           DECIMAL(10, 2)  NOT NULL DEFAULT 0
    -- subtotal = MAX(price, price_at_time) * quantity  (calculado en Python)
);


-- ============================================================
--  11. PEDIDOS (orders.Order)
-- ============================================================
CREATE TABLE IF NOT EXISTS orders_order (
    id              SERIAL PRIMARY KEY,
    client_id       INTEGER         NOT NULL REFERENCES accounts_user(id) ON DELETE CASCADE,
    driver_id       INTEGER         REFERENCES accounts_user(id) ON DELETE SET NULL,
    agency_id       INTEGER         REFERENCES agencies_agency(id)        ON DELETE SET NULL,
    coupon_id       INTEGER         REFERENCES coupons_coupon(id)         ON DELETE SET NULL,
    status          VARCHAR(15)     NOT NULL DEFAULT 'pending',
        -- Valores: 'pending' | 'accepted' | 'on_way' | 'delivered' | 'cancelled'
    total_amount    DECIMAL(10, 2)  NOT NULL DEFAULT 0,
    discount_amount DECIMAL(10, 2)  NOT NULL DEFAULT 0,
    delivery_address VARCHAR(255)   NOT NULL DEFAULT '',
    delivery_lat    DECIMAL(10, 6),
    delivery_lng    DECIMAL(10, 6),
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);


-- ============================================================
--  12. ÍTEMS DE PEDIDO (orders.OrderItem)
-- ============================================================
CREATE TABLE IF NOT EXISTS orders_orderitem (
    id          SERIAL PRIMARY KEY,
    order_id    INTEGER         NOT NULL REFERENCES orders_order(id)      ON DELETE CASCADE,
    product_id  INTEGER         NOT NULL REFERENCES products_product(id)  ON DELETE RESTRICT,
    quantity    INTEGER         NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price  DECIMAL(10, 2)  NOT NULL
    -- subtotal = unit_price * quantity  (calculado en Python)
);


-- ============================================================
--  13. HISTORIAL DE CAMBIOS DE ESTADO DE PEDIDO (orders.OrderLog)
-- ============================================================
CREATE TABLE IF NOT EXISTS orders_orderlog (
    id              SERIAL PRIMARY KEY,
    order_id        INTEGER         NOT NULL REFERENCES orders_order(id)   ON DELETE CASCADE,
    estado_anterior VARCHAR(15),
    estado_nuevo    VARCHAR(15)     NOT NULL,
    changed_by_id   INTEGER         REFERENCES accounts_user(id)          ON DELETE SET NULL,
    timestamp       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    nota            TEXT
);


-- ============================================================
--  14. INVENTARIO / MOVIMIENTOS DE STOCK (inventory.InventoryLog)
-- ============================================================
CREATE TABLE IF NOT EXISTS inventory_inventorylog (
    id              SERIAL PRIMARY KEY,
    product_id      INTEGER         NOT NULL REFERENCES products_product(id) ON DELETE CASCADE,
    user_id         INTEGER         REFERENCES accounts_user(id)             ON DELETE SET NULL,
    quantity        INTEGER         NOT NULL CHECK (quantity > 0),
    movement_type   VARCHAR(3)      NOT NULL,  -- 'IN' (entrada) | 'OUT' (salida)
    reason          VARCHAR(255)    NOT NULL DEFAULT '',
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);


-- ============================================================
--  15. ENTREGAS / DISTRIBUCIÓN (distribution.Delivery)
-- ============================================================
CREATE TABLE IF NOT EXISTS distribution_delivery (
    id              SERIAL PRIMARY KEY,
    order_id        INTEGER         NOT NULL UNIQUE REFERENCES orders_order(id) ON DELETE CASCADE,
    driver_id       INTEGER         REFERENCES accounts_user(id)                ON DELETE SET NULL,
    assigned_at     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    delivered_at    TIMESTAMP WITH TIME ZONE,
    notes           TEXT            NOT NULL DEFAULT ''
);


-- ============================================================
--  16. NOTIFICACIONES (notifications.Notification)
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications_notification (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER     NOT NULL REFERENCES accounts_user(id) ON DELETE CASCADE,
    order_id    INTEGER     REFERENCES orders_order(id)           ON DELETE CASCADE,
    message     TEXT        NOT NULL,
    is_read     BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);


-- ============================================================
--  17. VALORACIONES / RATINGS (ratings.Rating)
--      Un cliente puede valorar el producto o el repartidor
--      de un pedido específico.
-- ============================================================
CREATE TABLE IF NOT EXISTS ratings_rating (
    id              SERIAL PRIMARY KEY,
    user_client_id  INTEGER     NOT NULL REFERENCES accounts_user(id)    ON DELETE CASCADE,
    order_id        INTEGER     NOT NULL REFERENCES orders_order(id)     ON DELETE CASCADE,
    product_id      INTEGER     REFERENCES products_product(id)          ON DELETE CASCADE,
    driver_id       INTEGER     REFERENCES accounts_user(id)             ON DELETE CASCADE,
    score           INTEGER     NOT NULL CHECK (score >= 1 AND score <= 5),
    comment         TEXT        NOT NULL DEFAULT '',
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);


-- ============================================================
--  RESUMEN DE TABLAS
-- ============================================================
-- accounts_user                  → Usuarios del sistema (admin, agencia, cliente, repartidor)
-- accounts_user_groups           → M2M: Usuario ↔ Grupos Django
-- accounts_user_user_permissions → M2M: Usuario ↔ Permisos Django
-- accounts_passwordresetcode     → Códigos OTP de recuperación por WhatsApp
-- accounts_driverprofile         → Perfil extendido del repartidor
-- products_category              → Categorías de productos
-- products_product               → Catálogo de productos (bidones, dispensers, etc.)
-- agencies_agency                → Sucursales/agencias autorizadas
-- coupons_coupon                 → Cupones de descuento personalizados por cliente
-- promotions_promotion           → Promociones globales por porcentaje
-- promotions_promotion_products  → M2M: Promoción ↔ Productos incluidos
-- orders_cart                    → Carrito de compras (anónimo o autenticado)
-- orders_cartitem                → Productos dentro del carrito
-- orders_order                   → Pedidos realizados
-- orders_orderitem               → Productos dentro de un pedido
-- orders_orderlog                → Historial de cambios de estado del pedido
-- inventory_inventorylog         → Movimientos de stock (entradas/salidas)
-- distribution_delivery          → Asignación de entrega a repartidor
-- notifications_notification     → Notificaciones en tiempo real (Pusher)
-- ratings_rating                 → Valoraciones de productos y repartidores
