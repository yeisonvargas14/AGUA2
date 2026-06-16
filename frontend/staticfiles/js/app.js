document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------------------
    // Responsive Sidebar Toggle (Mobile) - Global initialization
    // -------------------------------------------------------------------------
    const sidebar       = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebarClose  = document.getElementById('sidebar-close');
    const menuItems     = document.querySelectorAll('.menu-item');

    function openSidebar() {
        if (sidebar && sidebarOverlay) {
            sidebar.classList.add('open');
            sidebarOverlay.classList.add('active');
            // Lock background scroll only while sidebar is open
            document.body.style.overflow = 'hidden';
            document.body.style.position = 'fixed';
            document.body.style.width = '100%';
        }
    }

    function closeSidebar() {
        if (sidebar && sidebarOverlay) {
            sidebar.classList.remove('open');
            sidebarOverlay.classList.remove('active');
            // CRITICAL: restore scroll — use 'auto' not '' to avoid inheritance conflicts
            document.body.style.overflow = 'auto';
            document.body.style.position = '';
            document.body.style.width = '';
        }
    }

    // Safety net: on page load, always ensure body is scrollable
    document.body.style.overflow = 'auto';
    document.body.style.position = '';

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', openSidebar);
        sidebarToggle.addEventListener('touchstart', (e) => {
            e.preventDefault();
            openSidebar();
        }, { passive: false });
    }

    if (sidebarClose) {
        sidebarClose.addEventListener('click', closeSidebar);
        sidebarClose.addEventListener('touchstart', (e) => {
            e.preventDefault();
            closeSidebar();
        }, { passive: false });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeSidebar);
        sidebarOverlay.addEventListener('touchstart', (e) => {
            e.preventDefault();
            closeSidebar();
        }, { passive: false });
    }

    // Close sidebar automatically when a menu item is selected on mobile
    menuItems.forEach(item => {
        item.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                closeSidebar();
            }
        });
    });

    // Re-enable scroll if window is resized above mobile breakpoint
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            closeSidebar();
        }
    });

    // -------------------------------------------------------------------------
    // Core App State & Navigation Setup (SPA Admin Dashboard Only)
    // -------------------------------------------------------------------------
    const adminDashboardContainer = document.querySelector('.admin-dashboard-container');
    if (!adminDashboardContainer) {
        return; // Do not initialize SPA on other pages or roles
    }

    const contentBody = document.querySelector('.content-body');
    const pageTitle = document.querySelector('.page-title');

    
    // Auto-seed database and load dashboard on initial start
    initApp();

    async function initApp() {
        // Run seed to populate DB if empty
        try {
            await fetch('/api/seed/');
        } catch (e) {
            console.error("Error seeding:", e);
        }
        // Load initial Dashboard
        loadDashboard();
    }

    // Set up Sidebar Menu Navigation
    menuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            const menuText = item.querySelector('span').innerText.trim().toLowerCase();
            const spaRoutes = ['dashboard', 'productos', 'inventario', 'agencias', 'distribución'];
            
            if (spaRoutes.includes(menuText)) {
                e.preventDefault();
                menuItems.forEach(i => i.classList.remove('active'));
                item.classList.add('active');

                if (menuText === 'dashboard') {
                    loadDashboard();
                } else if (menuText === 'productos') {
                    loadProducts();
                } else if (menuText === 'pedidos') {
                    loadOrders();
                } else if (menuText === 'inventario') {
                    loadInventory();
                } else if (menuText === 'agencias') {
                    loadAgencies();
                } else if (menuText === 'distribución') {
                    loadDistribution();
                }
            }
        });
    });

    // Wire global quick action button in top bar "Nuevo Pedido"
    const quickActionBtn = document.querySelector('.navbar .btn-primary');
    if (quickActionBtn) {
        quickActionBtn.addEventListener('click', () => {
            openNewOrderModal();
        });
    }

    // Setup Notification Alerts
    const notificationsBtn = document.getElementById('notifications-btn');
    if (notificationsBtn) {
        notificationsBtn.addEventListener('click', () => {
            const badge = notificationsBtn.querySelector('.badge');
            if (badge) badge.style.display = 'none';
            alert('Notificaciones de Stock:\n- Bidón de Agua 20L tiene bajo stock (15 unidades).\n- Nuevo pedido pendiente de aprobación.');
        });
    }

    // -------------------------------------------------------------------------
    // Helper to Render Premium Modals
    // -------------------------------------------------------------------------
    function showModal(title, htmlContent, onConfirm) {
        // Remove any existing modals first
        const existing = document.querySelector('.custom-modal-overlay');
        if (existing) existing.remove();

        const overlay = document.createElement('div');
        overlay.className = 'custom-modal-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(8px);
            display: flex; align-items: center; justify-content: center;
            z-index: 9999;
            animation: fadeIn 0.25s ease;
        `;

        const card = document.createElement('div');
        card.className = 'custom-modal-card';
        card.style.cssText = `
            background: #ffffff;
            border-radius: 16px;
            padding: 24px;
            width: 100%;
            max-width: 500px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            border: 1px solid rgba(226, 232, 240, 0.8);
            transform: scale(0.95);
            transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        `;

        card.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 20px; border-bottom: 1px solid #f1f5f9; padding-bottom: 12px;">
                <h3 style="font-family:'Outfit',sans-serif; font-size:1.25rem; font-weight:700; color:#0f172a;">${title}</h3>
                <button class="modal-close-btn" style="background:none; border:none; color:#64748b; font-size:1.2rem; cursor:pointer;"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="modal-body-content" style="margin-bottom: 24px;">
                ${htmlContent}
            </div>
            <div style="display:flex; justify-content:flex-end; gap:12px;">
                <button class="btn btn-secondary modal-cancel-btn" style="background:#f1f5f9; color:#475569; padding: 10px 18px; border:none; border-radius:8px; cursor:pointer; font-weight:500;">Cancelar</button>
                <button class="btn btn-primary modal-confirm-btn" style="background:#0284c7; color:#fff; padding: 10px 18px; border:none; border-radius:8px; cursor:pointer; font-weight:500;">Confirmar</button>
            </div>
        `;

        overlay.appendChild(card);
        document.body.appendChild(overlay);

        // Animation entry
        setTimeout(() => { card.style.transform = 'scale(1)'; }, 10);

        // Handlers
        const close = () => {
            card.style.transform = 'scale(0.95)';
            overlay.style.opacity = '0';
            setTimeout(() => overlay.remove(), 200);
        };

        overlay.querySelector('.modal-close-btn').addEventListener('click', close);
        overlay.querySelector('.modal-cancel-btn').addEventListener('click', close);
        
        const confirmBtn = overlay.querySelector('.modal-confirm-btn');
        confirmBtn.addEventListener('click', async () => {
            confirmBtn.disabled = true;
            confirmBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Guardando...';
            const success = await onConfirm(overlay);
            if (success) {
                close();
            } else {
                confirmBtn.disabled = false;
                confirmBtn.innerText = 'Confirmar';
            }
        });
    }

    // -------------------------------------------------------------------------
    // MODULE 1: Dashboard Loading & Render
    // -------------------------------------------------------------------------
    async function loadDashboard() {
        pageTitle.innerText = "Dashboard de Control";
        contentBody.innerHTML = `
            <div style="display:flex; justify-content:center; align-items:center; height: 200px;">
                <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 2.5rem; color: #0284c7;"></i>
            </div>
        `;

        try {
            // Parallel fetches for efficiency
            const [statsRes, ordersRes, productsRes] = await Promise.all([
                fetch('/api/stats/'),
                fetch('/api/orders/'),
                fetch('/api/products/')
            ]);

            const stats = await statsRes.json();
            const orders = await ordersRes.json();
            const products = await productsRes.json();

            // Render stats grid, orders table, stock list
            contentBody.innerHTML = `
                <!-- Dashboard Statistics Cards -->
                <div class="dashboard-grid">
                    <div class="stat-card">
                        <div class="card-icon blue">
                            <i class="fa-solid fa-cubes"></i>
                        </div>
                        <div class="card-data">
                            <span class="card-label">Pedidos Registrados</span>
                            <span class="card-value">${stats.orders_count}</span>
                        </div>
                        <div class="card-trend up">
                            <i class="fa-solid fa-circle-info"></i> Activos
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="card-icon emerald">
                            <i class="fa-solid fa-dollar-sign"></i>
                        </div>
                        <div class="card-data">
                            <span class="card-label">Ingresos Totales</span>
                            <span class="card-value">Bs. ${stats.monthly_income.toFixed(2)}</span>
                        </div>
                        <div class="card-trend up">
                            <i class="fa-solid fa-arrow-trend-up"></i> Entregados
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="card-icon orange">
                            <i class="fa-solid fa-truck"></i>
                        </div>
                        <div class="card-data">
                            <span class="card-label">En Distribución</span>
                            <span class="card-value">${stats.active_deliveries}</span>
                        </div>
                        <div class="card-trend" style="color: #ea580c;">
                            <i class="fa-solid fa-truck-ramp-box"></i> En ruta
                        </div>
                    </div>
                </div>

                <!-- Main Layout Grid -->
                <div class="dashboard-sections">
                    
                    <!-- Table: Recent Orders -->
                    <div class="section-card">
                        <div class="section-header">
                            <h3 class="section-title">Pedidos Recientes</h3>
                            <button id="view-all-orders" class="btn btn-text" style="color: #0284c7; background: none; border: none; font-weight: 600; cursor: pointer;">Ver todos</button>
                        </div>
                        <div class="table-responsive">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Cliente</th>
                                        <th>Estado</th>
                                        <th>Total</th>
                                        <th>Fecha</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${orders.slice(0, 4).map(o => `
                                        <tr>
                                            <td><strong>#${o.id}</strong></td>
                                            <td><div class="td-user"><span class="name">${o.user}</span></div></td>
                                            <td><span class="badge badge-${getStatusClass(o.status)}">${o.status_display}</span></td>
                                            <td>Bs. ${o.total_amount.toFixed(2)}</td>
                                            <td style="color: #64748b; font-size: 0.85rem;">${o.created_at}</td>
                                        </tr>
                                    `).join('') || '<tr><td colspan="5" style="text-align:center; padding: 24px; color:#64748b;">No hay pedidos registrados</td></tr>'}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Products Inventory List -->
                    <div class="section-card">
                        <div class="section-header">
                            <h3 class="section-title">Niveles de Stock</h3>
                            <span class="badge" style="background: ${stats.low_stock_count > 0 ? '#fef2f2' : '#ecfdf5'}; color: ${stats.low_stock_count > 0 ? '#ef4444' : '#10b981'}; font-weight:600;">
                                ${stats.low_stock_count} Alertas de Stock
                            </span>
                        </div>
                        <div class="product-stock-list">
                            ${products.slice(0, 3).map(p => {
                                const percentage = Math.min(100, Math.max(0, (p.stock / 400) * 100));
                                const isLow = p.stock <= 20;
                                return `
                                    <div class="stock-item" style="margin-bottom: 16px;">
                                        <div class="stock-info" style="display:flex; justify-content:space-between; margin-bottom: 6px;">
                                            <span class="prod-name" style="font-weight:600; color:#334155;">${p.name}</span>
                                            <span class="prod-stock ${isLow ? 'warning' : 'success'}" style="font-weight:600; color: ${isLow ? '#f59e0b' : '#10b981'};">
                                                ${isLow ? 'Bajo Stock: ' : ''}${p.stock} unidades
                                            </span>
                                        </div>
                                        <div class="progress-bar" style="background:#e2e8f0; border-radius:8px; height:8px; overflow:hidden;">
                                            <div class="progress" style="width: ${percentage}%; background: ${isLow ? '#f59e0b' : '#10b981'}; height:100%; border-radius:8px;"></div>
                                        </div>
                                    </div>
                                `;
                            }).join('') || '<div style="text-align:center; color:#64748b; padding:24px;">No hay productos registrados</div>'}
                        </div>
                    </div>
                </div>
            `;

            // Wire "Ver todos" button
            document.getElementById('view-all-orders').addEventListener('click', () => {
                const navItem = Array.from(menuItems).find(i => i.querySelector('span').innerText.trim().toLowerCase() === 'pedidos');
                if (navItem) navItem.click();
            });

        } catch (e) {
            contentBody.innerHTML = `
                <div style="background:#fef2f2; border:1px solid #fee2e2; border-radius:12px; padding:20px; color:#b91c1c; font-weight:500;">
                    <i class="fa-solid fa-circle-exclamation"></i> Error al cargar datos del Dashboard: ${e.message}
                </div>
            `;
        }
    }

    // -------------------------------------------------------------------------
    // MODULE 2: Products Management
    // -------------------------------------------------------------------------
    async function loadProducts() {
        pageTitle.innerText = "Catálogo de Productos";
        contentBody.innerHTML = `
            <div style="display:flex; justify-content:center; align-items:center; height: 200px;">
                <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 2.5rem; color: #0284c7;"></i>
            </div>
        `;

        try {
            const res = await fetch('/api/products/');
            const products = await res.json();

            contentBody.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 24px;">
                    <p style="color:#64748b; font-weight:500;">Administra los productos de agua purificada y accesorios.</p>
                    <button class="btn btn-primary" id="add-product-btn" style="display:flex; align-items:center; gap:8px;">
                        <i class="fa-solid fa-plus"></i> Añadir Producto
                    </button>
                </div>

                <div class="products-grid" style="display:grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap:24px;">
                    ${products.map(p => `
                        <div class="product-card" style="background:#fff; border-radius:16px; padding:20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border:1px solid #f1f5f9; position:relative; display:flex; flex-direction:column; justify-content:space-between;">
                            <div>
                                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
                                    <h4 style="font-family:'Outfit',sans-serif; font-size:1.15rem; font-weight:700; color:#0f172a;">${p.name}</h4>
                                    <span class="badge" style="background:#f0f9ff; color:#0284c7; font-weight:700; font-size:1rem; padding:4px 8px;">Bs. ${p.price.toFixed(2)}</span>
                                </div>
                                <p style="color:#64748b; font-size:0.875rem; line-height:1.5; margin-bottom:16px;">${p.description || 'Sin descripción.'}</p>
                            </div>
                            <div>
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:12px; border-top:1px solid #f8fafc; padding-top:12px;">
                                    <span style="font-size:0.85rem; font-weight:600; color:${p.stock <= 20 ? '#ea580c' : '#475569'};">
                                        <i class="fa-solid fa-boxes-stacked"></i> Stock: ${p.stock} u.
                                    </span>
                                    <div style="display:flex; gap:8px;">
                                        <button class="btn-edit-product" data-id="${p.id}" style="background:#f0fdf4; border:none; color:#16a34a; width:32px; height:32px; border-radius:8px; cursor:pointer; display:flex; align-items:center; justify-content:center;" title="Editar"><i class="fa-solid fa-pen"></i></button>
                                        <button class="btn-delete-product" data-id="${p.id}" style="background:#fef2f2; border:none; color:#dc2626; width:32px; height:32px; border-radius:8px; cursor:pointer; display:flex; align-items:center; justify-content:center;" title="Eliminar"><i class="fa-solid fa-trash"></i></button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('') || '<div style="grid-column: 1/-1; text-align:center; padding:48px; color:#64748b;">No hay productos registrados en el catálogo.</div>'}
                </div>
            `;

            // Wire Add Product button
            document.getElementById('add-product-btn').addEventListener('click', openAddProductModal);

            // Wire Edit & Delete actions
            document.querySelectorAll('.btn-edit-product').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const id = btn.getAttribute('data-id');
                    const prod = products.find(p => p.id == id);
                    openEditProductModal(prod);
                });
            });

            document.querySelectorAll('.btn-delete-product').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const id = btn.getAttribute('data-id');
                    if (confirm('¿Estás seguro de eliminar este producto?')) {
                        const res = await fetch(`/api/products/${id}/`, { method: 'DELETE' });
                        if (res.ok) {
                            loadProducts();
                        } else {
                            alert('No se pudo eliminar el producto.');
                        }
                    }
                });
            });

        } catch (e) {
            contentBody.innerHTML = `<div style="color:red;">Error: ${e.message}</div>`;
        }
    }

    function openAddProductModal() {
        const formHtml = `
            <div style="display:flex; flex-direction:column; gap:16px;">
                <div>
                    <label style="display:block; font-weight:600; margin-bottom:6px; color:#475569;">Nombre del Producto</label>
                    <input type="text" id="prod-name" placeholder="Ej: Bidón 20L" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:8px; outline:none; font-family:inherit;">
                </div>
                <div>
                    <label style="display:block; font-weight:600; margin-bottom:6px; color:#475569;">Precio (Bs.)</label>
                    <input type="number" id="prod-price" step="0.1" placeholder="Ej: 12.00" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:8px; outline:none; font-family:inherit;">
                </div>
                <div>
                    <label style="display:block; font-weight:600; margin-bottom:6px; color:#475569;">Stock Inicial</label>
                    <input type="number" id="prod-stock" placeholder="Ej: 100" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:8px; outline:none; font-family:inherit;">
                </div>
                <div>
                    <label style="display:block; font-weight:600; margin-bottom:6px; color:#475569;">Descripción</label>
                    <textarea id="prod-desc" rows="3" placeholder="Detalles o especificaciones..." style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:8px; outline:none; font-family:inherit; resize:none;"></textarea>
                </div>
            </div>
        `;

        showModal('Nuevo Producto', formHtml, async (modalOverlay) => {
            const name = modalOverlay.querySelector('#prod-name').value;
            const price = modalOverlay.querySelector('#prod-price').value;
            const stock = modalOverlay.querySelector('#prod-stock').value;
            const description = modalOverlay.querySelector('#prod-desc').value;

            if (!name || !price || !stock) {
                alert('Por favor complete los campos requeridos.');
                return false;
            }

            try {
                const res = await fetch('/api/products/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, price: parseFloat(price), stock: parseInt(stock), description })
                });
                if (res.ok) {
                    loadProducts();
                    return true;
                }
            } catch (e) {
                alert('Error al guardar el producto.');
            }
            return false;
        });
    }

    function openEditProductModal(product) {
        const formHtml = `
            <div style="display:flex; flex-direction:column; gap:16px;">
                <input type="hidden" id="prod-id" value="${product.id}">
                <div>
                    <label style="display:block; font-weight:600; margin-bottom:6px; color:#475569;">Nombre del Producto</label>
                    <input type="text" id="prod-name" value="${product.name}" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:8px; outline:none;">
                </div>
                <div>
                    <label style="display:block; font-weight:600; margin-bottom:6px; color:#475569;">Precio (Bs.)</label>
                    <input type="number" id="prod-price" step="0.1" value="${product.price}" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:8px; outline:none;">
                </div>
                <div>
                    <label style="display:block; font-weight:600; margin-bottom:6px; color:#475569;">Stock Actual</label>
                    <input type="number" id="prod-stock" value="${product.stock}" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:8px; outline:none;">
                </div>
                <div>
                    <label style="display:block; font-weight:600; margin-bottom:6px; color:#475569;">Descripción</label>
                    <textarea id="prod-desc" rows="3" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:8px; resize:none;">${product.description}</textarea>
                </div>
            </div>
        `;

        showModal('Editar Producto', formHtml, async (modalOverlay) => {
            const name = modalOverlay.querySelector('#prod-name').value;
            const price = modalOverlay.querySelector('#prod-price').value;
            const stock = modalOverlay.querySelector('#prod-stock').value;
            const description = modalOverlay.querySelector('#prod-desc').value;

            try {
                const res = await fetch(`/api/products/${product.id}/`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, price: parseFloat(price), stock: parseInt(stock), description })
                });
                if (res.ok) {
                    loadProducts();
                    return true;
                }
            } catch (e) {
                alert('Error al actualizar el producto.');
            }
            return false;
        });
    }


    // -------------------------------------------------------------------------
    // MODULE 3: Orders Registry
    // -------------------------------------------------------------------------
    async function loadOrders() {
        pageTitle.innerText = "Registro de Pedidos";
        contentBody.innerHTML = `
            <div style="display:flex; justify-content:center; align-items:center; height: 200px;">
                <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 2.5rem; color: #0284c7;"></i>
            </div>
        `;

        try {
            const res = await fetch('/api/orders/');
            const orders = await res.json();

            contentBody.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 24px;">
                    <p style="color:#64748b; font-weight: 500;">Historial y control de despachos de agua.</p>
                    <button class="btn btn-primary" id="new-order-btn" style="display:flex; align-items:center; gap:8px;">
                        <i class="fa-solid fa-plus"></i> Registrar Pedido
                    </button>
                </div>

                <div class="section-card">
                    <div class="table-responsive">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Cliente</th>
                                    <th>Productos solicitados</th>
                                    <th>Dirección de Envío</th>
                                    <th>Total</th>
                                    <th>Fecha</th>
                                    <th>Estado</th>
                                    <th>Acción</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${orders.map(o => `
                                    <tr>
                                        <td><strong>#${o.id}</strong></td>
                                        <td><span class="name" style="font-weight:600; color:#334155;">${o.user}</span></td>
                                        <td>
                                            <ul style="margin:0; padding:0 0 0 16px; font-size:0.875rem; color:#475569;">
                                                ${o.items.map(item => `<li>${item.quantity} x ${item.product_name}</li>`).join('')}
                                            </ul>
                                        </td>
                                        <td style="color:#64748b; font-size:0.875rem;">${o.delivery_address || 'Agencia'}</td>
                                        <td style="font-weight: 700; color:#0f172a;">Bs. ${o.total_amount.toFixed(2)}</td>
                                        <td style="color:#64748b; font-size:0.85rem;">${o.created_at}</td>
                                        <td><span class="badge badge-${getStatusClass(o.status)}">${o.status_display}</span></td>
                                        <td>
                                            <select class="order-status-select" data-id="${o.id}" style="padding:6px 10px; border-radius:8px; border:1px solid #cbd5e1; outline:none; background:#f8fafc; cursor:pointer; font-size:0.85rem; font-weight:500;">
                                                <option value="pending" ${o.status === 'pending' ? 'selected' : ''}>Pendiente</option>
                                                <option value="accepted" ${o.status === 'accepted' ? 'selected' : ''}>Aceptado</option>
                                                <option value="on_way" ${o.status === 'on_way' ? 'selected' : ''}>En camino</option>
                                                <option value="delivered" ${o.status === 'delivered' ? 'selected' : ''}>Entregado</option>
                                                <option value="cancelled" ${o.status === 'cancelled' ? 'selected' : ''}>Cancelado</option>
                                            </select>
                                        </td>
                                    </tr>
                                `).join('') || '<tr><td colspan="8" style="text-align:center; padding:36px; color:#64748b;">No hay pedidos registrados</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;

            // Wire New Order button
            document.getElementById('new-order-btn').addEventListener('click', openNewOrderModal);

            // Wire select changes to update status
            document.querySelectorAll('.order-status-select').forEach(select => {
                select.addEventListener('change', async (e) => {
                    const id = select.getAttribute('data-id');
                    const newStatus = select.value;
                    try {
                        const res = await fetch(`/api/orders/${id}/status/`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ status: newStatus })
                        });
                        if (res.ok) {
                            loadOrders();
                        } else {
                            alert('No se pudo actualizar el estado del pedido.');
                        }
                    } catch (err) {
                        alert('Error de conexión.');
                    }
                });
            });

        } catch (e) {
            contentBody.innerHTML = `<div style="color:red;">Error: ${e.message}</div>`;
        }
    }

    async function openNewOrderModal() {
        // Fetch products first to list them in the order form
        try {
            const res = await fetch('/api/products/');
            const products = await res.json();

            const formHtml = `
                <div style="display:flex; flex-direction:column; gap:16px;">
                    <div>
                        <label style="display:block; font-weight:600; margin-bottom:6px; color:#475569;">Producto</label>
                        <select id="ord-product-id" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:8px; background:#fff; font-family:inherit;">
                            ${products.map(p => `<option value="${p.id}">${p.name} - Bs. ${p.price.toFixed(2)} (Stock: ${p.stock})</option>`).join('')}
                        </select>
                    </div>
                    <div>
                        <label style="display:block; font-weight:600; margin-bottom:6px; color:#475569;">Cantidad</label>
                        <input type="number" id="ord-qty" value="1" min="1" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:8px;">
                    </div>
                    <div>
                        <label style="display:block; font-weight:600; margin-bottom:6px; color:#475569;">Dirección de Entrega</label>
                        <input type="text" id="ord-address" placeholder="Ej: Calle Comercio #145" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:8px;">
                    </div>
                    <div>
                        <label style="display:block; font-weight:600; margin-bottom:6px; color:#475569;">Estado del Pedido</label>
                        <select id="ord-status" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:8px; background:#fff;">
                            <option value="pending">Pendiente</option>
                            <option value="accepted">Aceptado</option>
                            <option value="on_way">En camino</option>
                        </select>
                    </div>
                </div>
            `;

            showModal('Nuevo Pedido', formHtml, async (modalOverlay) => {
                const productId = modalOverlay.querySelector('#ord-product-id').value;
                const quantity = modalOverlay.querySelector('#ord-qty').value;
                const address = modalOverlay.querySelector('#ord-address').value;
                const status = modalOverlay.querySelector('#ord-status').value;

                if (!productId || !quantity || !address) {
                    alert('Por favor complete todos los datos.');
                    return false;
                }

                try {
                    const res = await fetch('/api/orders/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            status,
                            delivery_address: address,
                            items: [
                                { product_id: parseInt(productId), quantity: parseInt(quantity) }
                            ]
                        })
                    });
                    if (res.ok) {
                        // Check if current view is orders or dashboard, reload active
                        const activeItem = document.querySelector('.menu-item.active').querySelector('span').innerText.trim().toLowerCase();
                        if (activeItem === 'pedidos') {
                            loadOrders();
                        } else {
                            loadDashboard();
                        }
                        return true;
                    } else {
                        const err = await res.json();
                        alert('Error: ' + err.message);
                    }
                } catch (e) {
                    alert('Error al registrar pedido.');
                }
                return false;
            });

        } catch (e) {
            alert('No se pudo cargar la lista de productos.');
        }
    }


    // -------------------------------------------------------------------------
    // MODULE 4: Inventory & Stock Log
    // -------------------------------------------------------------------------
    async function loadInventory() {
        pageTitle.innerText = "Historial de Inventario";
        contentBody.innerHTML = `
            <div style="display:flex; justify-content:center; align-items:center; height: 200px;">
                <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 2.5rem; color: #0284c7;"></i>
            </div>
        `;

        try {
            const res = await fetch('/api/inventory/');
            const logs = await res.json();

            contentBody.innerHTML = `
                <p style="color:#64748b; margin-bottom: 24px; font-weight: 500;">
                    Bitácora en tiempo real de entradas y salidas de stock del almacén.
                </p>

                <div class="section-card">
                    <div class="table-responsive">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Producto</th>
                                    <th>Movimiento</th>
                                    <th>Cantidad</th>
                                    <th>Motivo/Detalle</th>
                                    <th>Operador</th>
                                    <th>Fecha</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${logs.map(log => `
                                    <tr>
                                        <td>#${log.id}</td>
                                        <td><strong style="color:#0f172a;">${log.product_name}</strong></td>
                                        <td>
                                            <span class="badge" style="background: ${log.movement_type === 'IN' ? '#ecfdf5' : '#fff7ed'}; color: ${log.movement_type === 'IN' ? '#10b981' : '#f97316'}; font-weight:700;">
                                                <i class="fa-solid ${log.movement_type === 'IN' ? 'fa-arrow-trend-up' : 'fa-arrow-trend-down'}"></i> ${log.movement_display}
                                            </span>
                                        </td>
                                        <td style="font-weight:700;">${log.quantity} u.</td>
                                        <td style="color:#64748b; font-size:0.875rem;">${log.reason || 'Sincronización'}</td>
                                        <td style="font-weight:500; color:#475569;">${log.user}</td>
                                        <td style="color:#64748b; font-size:0.85rem;">${log.created_at}</td>
                                    </tr>
                                `).join('') || '<tr><td colspan="7" style="text-align:center; padding:36px; color:#64748b;">No hay registros de inventario.</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } catch (e) {
            contentBody.innerHTML = `<div style="color:red;">Error: ${e.message}</div>`;
        }
    }


    // -------------------------------------------------------------------------
    // MODULE 5: Agencies List
    // -------------------------------------------------------------------------
    async function loadAgencies() {
        pageTitle.innerText = "Agencias de Distribución";
        contentBody.innerHTML = `
            <div style="display:flex; justify-content:center; align-items:center; height: 200px;">
                <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 2.5rem; color: #0284c7;"></i>
            </div>
        `;

        try {
            const res = await fetch('/api/agencies/');
            const agencies = await res.json();

            contentBody.innerHTML = `
                <p style="color:#64748b; margin-bottom: 24px; font-weight: 500;">
                    Sucursales autorizadas para entrega y almacenamiento en Comarapa y alrededores.
                </p>

                <div class="products-grid" style="display:grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap:24px;">
                    ${agencies.map(a => `
                        <div class="product-card" style="background:#fff; border-radius:16px; padding:24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border:1px solid #f1f5f9; display:flex; flex-direction:column; justify-content:space-between; gap:16px;">
                            <div>
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                                    <h4 style="font-family:'Outfit',sans-serif; font-size:1.25rem; font-weight:700; color:#0f172a;">${a.name}</h4>
                                    <span class="badge badge-success" style="font-weight:600;">Activo</span>
                                </div>
                                <p style="color:#64748b; font-size:0.875rem;"><i class="fa-solid fa-location-dot" style="color:#0284c7; margin-right:8px;"></i> ${a.address}</p>
                            </div>
                            <div style="background:#f8fafc; border-radius:12px; padding:12px; display:flex; align-items:center; gap:12px;">
                                <div style="background:#e0f2fe; width:36px; height:36px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#0284c7;">
                                    <i class="fa-solid fa-user-tie"></i>
                                </div>
                                <div>
                                    <span style="display:block; font-size:0.75rem; color:#64748b; font-weight:600; text-transform:uppercase;">Administrador</span>
                                    <span style="font-weight:600; color:#334155; font-size:0.9rem;">${a.manager}</span>
                                </div>
                            </div>
                        </div>
                    `).join('') || '<div style="grid-column:1/-1; text-align:center; padding:48px; color:#64748b;">No hay agencias registradas</div>'}
                </div>
            `;
        } catch (e) {
            contentBody.innerHTML = `<div style="color:red;">Error: ${e.message}</div>`;
        }
    }


    // -------------------------------------------------------------------------
    // MODULE 6: Logistics & Distribution
    // -------------------------------------------------------------------------
    async function loadDistribution() {
        pageTitle.innerText = "Logística de Distribución";
        contentBody.innerHTML = `
            <div style="display:flex; justify-content:center; align-items:center; height: 200px;">
                <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 2.5rem; color: #0284c7;"></i>
            </div>
        `;

        try {
            const res = await fetch('/api/deliveries/');
            const deliveries = await res.json();

            contentBody.innerHTML = `
                <p style="color:#64748b; margin-bottom: 24px; font-weight: 500;">
                    Seguimiento satelital y estado de despachos a cargo de los repartidores.
                </p>

                <div class="section-card">
                    <div class="table-responsive">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Pedido ID</th>
                                    <th>Cliente</th>
                                    <th>Dirección</th>
                                    <th>Chofer / Repartidor</th>
                                    <th>Asignado en</th>
                                    <th>Estado de Entrega</th>
                                    <th>Notas de Despacho</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${deliveries.map(d => `
                                    <tr>
                                        <td><strong>#${d.order_id}</strong></td>
                                        <td style="font-weight:600; color:#334155;">${d.client_name}</td>
                                        <td style="font-size:0.875rem; color:#475569;">${d.delivery_address}</td>
                                        <td>
                                            <div style="display:flex; align-items:center; gap:8px; font-weight:500;">
                                                <i class="fa-solid fa-id-card" style="color:#64748b;"></i> ${d.driver}
                                            </div>
                                        </td>
                                        <td style="color:#64748b; font-size:0.85rem;">${d.assigned_at}</td>
                                        <td>
                                            <span class="badge" style="background:#e0f2fe; color:#0369a1; font-weight:700;">
                                                <i class="fa-solid fa-circle-info"></i> ${d.status_display}
                                            </span>
                                        </td>
                                        <td style="color:#64748b; font-size:0.875rem; max-width: 200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
                                            ${d.notes || 'Ninguna'}
                                        </td>
                                    </tr>
                                `).join('') || '<tr><td colspan="7" style="text-align:center; padding:36px; color:#64748b;">No hay despachos activos en curso.</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } catch (e) {
            contentBody.innerHTML = `<div style="color:red;">Error: ${e.message}</div>`;
        }
    }


    // -------------------------------------------------------------------------
    // Utility functions
    // -------------------------------------------------------------------------
    function getStatusClass(status) {
        switch (status) {
            case 'PENDING': return 'info';
            case 'PREPARING': return 'warning';
            case 'SHIPPED': return 'warning';
            case 'DELIVERED': return 'success';
            case 'CANCELLED': return 'danger';
            default: return 'info';
        }
    }

});

