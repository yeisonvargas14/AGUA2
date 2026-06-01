document.addEventListener('DOMContentLoaded', () => {
    // Menu navigation active state transitions
    const menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            menuItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
        });
    });

    // Notify icon alert animation
    const notificationsBtn = document.getElementById('notifications-btn');
    if (notificationsBtn) {
        notificationsBtn.addEventListener('click', () => {
            const badge = notificationsBtn.querySelector('.badge');
            if (badge) {
                badge.style.display = 'none';
            }
            alert('¡Tienes 3 nuevas notificaciones de inventario!');
        });
    }
});
