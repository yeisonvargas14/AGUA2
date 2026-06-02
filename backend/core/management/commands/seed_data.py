from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from accounts.models import User
from products.models import Product
from agencies.models import Agency
from coupons.models import Coupon
from promotions.models import Promotion
from orders.models import Order, OrderItem
from ratings.models import Rating
from inventory.models import InventoryLog
from distribution.models import Delivery

class Command(BaseCommand):
    help = 'Seeds sample data into the database for demonstration'

    def handle(self, *args, **kwargs):
        self.stdout.write("Empezando el sembrado de datos (Seeding)...")

        # 1. Clear database
        Rating.objects.all().delete()
        Delivery.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        InventoryLog.objects.all().delete()
        Coupon.objects.all().delete()
        Promotion.objects.all().delete()
        Agency.objects.all().delete()
        Product.objects.all().delete()
        
        # Keep superusers, delete others to avoid integrity issues
        User.objects.filter(is_superuser=False).delete()

        # 2. Create Users
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@aquaflow.com',
                'first_name': 'Administrador',
                'last_name': 'AquaFlow',
                'role': User.Roles.ADMIN,
                'phone': '+591 70000001',
                'address': 'Calle Central 100, Comarapa',
                'municipio': 'Comarapa'
            }
        )
        if created:
            admin_user.set_password('adminpassword')
            admin_user.save()

        agency_manager = User.objects.create(
            username='agente1',
            email='agente1@aquaflow.com',
            first_name='Juan',
            last_name='Pérez',
            role=User.Roles.AGENCY,
            phone='+591 70000002',
            address='Av. Santa Cruz 45, Comarapa',
            municipio='Comarapa'
        )
        agency_manager.set_password('agentepassword')
        agency_manager.save()

        driver_user = User.objects.create(
            username='repartidor1',
            email='rep1@aquaflow.com',
            first_name='Carlos',
            last_name='Gómez',
            role=User.Roles.DRIVER,
            phone='+591 70000003',
            address='Calle Bolívar 25, Comarapa',
            municipio='Comarapa'
        )
        driver_user.set_password('driverpassword')
        driver_user.save()

        client_user = User.objects.create(
            username='cliente1',
            email='cliente1@aquaflow.com',
            first_name='María',
            last_name='López',
            role=User.Roles.CLIENT,
            phone='+591 70000004',
            address='Av. Circunvalación #10, Comarapa',
            municipio='Comarapa'
        )
        client_user.set_password('clientpassword')
        client_user.save()

        self.stdout.write("Usuarios creados con éxito.")

        # 3. Create Products
        p1 = Product.objects.create(
            name="Bidón de Agua Purificada 20L",
            description="Bidón de 20 litros de agua purificada de la más alta calidad, con envase retornable.",
            price=Decimal("12.00"),
            stock=150,
            is_active=True
        )
        InventoryLog.objects.create(product=p1, user=admin_user, quantity=150, movement_type='IN', reason='Stock Inicial')

        p2 = Product.objects.create(
            name="Botella de Agua 500ml (Pack x6)",
            description="Práctico paquete de 6 botellas de agua purificada de 500ml, ideal para llevar a cualquier parte.",
            price=Decimal("15.00"),
            stock=300,
            is_active=True
        )
        InventoryLog.objects.create(product=p2, user=admin_user, quantity=300, movement_type='IN', reason='Stock Inicial')

        p3 = Product.objects.create(
            name="Dispenser de Agua Manual",
            description="Bomba de agua manual y de fácil instalación para bidones de 20 litros.",
            price=Decimal("35.00"),
            stock=12,
            is_active=True
        )
        InventoryLog.objects.create(product=p3, user=admin_user, quantity=12, movement_type='IN', reason='Stock Inicial')

        p4 = Product.objects.create(
            name="Bidón de Agua Purificada 10L",
            description="Presentación mediana de 10 litros con grifo incorporado, perfecto para hogares pequeños.",
            price=Decimal("7.00"),
            stock=80,
            is_active=True
        )
        InventoryLog.objects.create(product=p4, user=admin_user, quantity=80, movement_type='IN', reason='Stock Inicial')

        self.stdout.write("Productos creados con éxito.")

        # 4. Create Agency
        agency = Agency.objects.create(
            name="Agencia Zona Central - Comarapa",
            address="Av. Santa Cruz 45, Comarapa",
            manager=agency_manager,
            latitude=Decimal("-17.912300"),
            longitude=Decimal("-64.491200")
        )
        self.stdout.write("Agencia creada con éxito.")

        # 5. Create Coupon
        coupon = Coupon.objects.create(
            code="BIENVENIDA15",
            user_client=client_user,
            discount_percentage=15,
            expires_at=timezone.now() + timezone.timedelta(days=30),
            used=False
        )
        
        # An expired coupon
        Coupon.objects.create(
            code="PROMOEXPIRADA",
            user_client=client_user,
            discount_percentage=50,
            expires_at=timezone.now() - timezone.timedelta(days=1),
            used=False
        )
        
        self.stdout.write("Cupones creados con éxito.")

        # 6. Create Promotion
        promo = Promotion.objects.create(
            name="Descuento de Invierno en Bidones",
            description="10% de descuento directo en todos los bidones de 20L",
            discount_percentage=10,
            start_date=timezone.now() - timezone.timedelta(days=2),
            end_date=timezone.now() + timezone.timedelta(days=10),
            is_active=True
        )
        promo.products.add(p1)

        self.stdout.write("Promociones creadas con éxito.")

        # 7. Create Orders & Deliveries & Ratings
        # Order 1: Delivered
        o1 = Order.objects.create(
            client=client_user,
            driver=driver_user,
            agency=agency,
            total_amount=Decimal("39.00"),
            discount_amount=Decimal("0.00"),
            delivery_address="Calle Comercio #120, Comarapa",
            delivery_lat=Decimal("-17.912500"),
            delivery_lng=Decimal("-64.492000"),
            status=Order.Status.DELIVERED
        )
        OrderItem.objects.create(order=o1, product=p1, quantity=2, unit_price=Decimal("12.00"))
        OrderItem.objects.create(order=o1, product=p2, quantity=1, unit_price=Decimal("15.00"))
        
        d1 = Delivery.objects.create(
            order=o1,
            driver=driver_user,
            delivered_at=timezone.now() - timezone.timedelta(hours=5),
            notes="Entregado a la dueña de casa de forma cordial."
        )

        Rating.objects.create(
            user_client=client_user,
            order=o1,
            product=p1,
            score=5,
            comment="Excelente calidad de agua, bidón limpio."
        )
        Rating.objects.create(
            user_client=client_user,
            order=o1,
            driver=driver_user,
            score=5,
            comment="Excelente trato del repartidor, muy puntual."
        )

        # Order 2: On Way
        o2 = Order.objects.create(
            client=client_user,
            driver=driver_user,
            agency=agency,
            total_amount=Decimal("15.00"),
            discount_amount=Decimal("0.00"),
            delivery_address="Barrio Lindo, Comarapa",
            delivery_lat=Decimal("-17.915000"),
            delivery_lng=Decimal("-64.496000"),
            status=Order.Status.ON_WAY
        )
        OrderItem.objects.create(order=o2, product=p2, quantity=1, unit_price=Decimal("15.00"))
        
        Delivery.objects.create(
            order=o2,
            driver=driver_user,
            notes="En ruta con el pack."
        )

        # Order 3: Pending
        o3 = Order.objects.create(
            client=client_user,
            agency=agency,
            total_amount=Decimal("24.00"),
            discount_amount=Decimal("0.00"),
            delivery_address="Plaza Principal #5, Comarapa",
            delivery_lat=Decimal("-17.911000"),
            delivery_lng=Decimal("-64.490500"),
            status=Order.Status.PENDING
        )
        OrderItem.objects.create(order=o3, product=p1, quantity=2, unit_price=Decimal("12.00"))

        self.stdout.write("Pedidos de prueba sembrados.")
        self.stdout.write(self.style.SUCCESS("¡Sembrado de datos finalizado con éxito!"))
