from django.db import migrations, models


def finalize_catalog(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    Product = apps.get_model('products', 'Product')

    # Ensure exact categories
    cat_names = ['Productos', 'Dispensadores', 'Compras nuevas', 'Accesorios']
    cats = {}
    for name in cat_names:
        obj, _ = Category.objects.get_or_create(name=name)
        cats[name] = obj

    # Desired products list
    desired = [
        # Productos
        {
            'name': 'Botella de Agua 600ml (Pack x9)',
            'price': 35.00,
            'description': 'Paquete de 9 botellas de agua purificada de 600ml.',
            'category': cats['Productos'],
            'stock': 100,
            'is_active': True,
        },
        {
            'name': 'Bidón de Agua Purificada 10L (solo agua)',
            'price': 5.00,
            'description': 'Bidón de 10 litros de agua purificada, envase retornable. (Sin grifo)',
            'category': cats['Productos'],
            'stock': 500,
            'is_active': True,
        },
        {
            'name': 'Sachet de Agua 250ml (Paquete de 20)',
            'price': 10.00,
            'description': 'Paquete con 20 sachets de agua purificada de 250ml.',
            'category': cats['Productos'],
            'stock': 100,
            'is_active': True,
        },
        {
            'name': 'Botella de 6 litros',
            'price': 10.00,
            'description': 'Botella retornable de 6 litros de agua purificada.',
            'category': cats['Productos'],
            'stock': 100,
            'is_active': True,
        },
        # Bidón retornable 20L (maintain or create)
        {
            'name': 'Bidón de Agua Purificada 20L (retornable)',
            'price': 12.00,
            'description': 'Bidón de 20 litros de agua purificada, envase retornable.',
            'category': cats['Productos'],
            'stock': 500,
            'is_active': True,
        },

        # Dispensadores
        {
            'name': 'Dispenser de Agua Manual',
            'price': 35.00,
            'description': 'Bomba manual para bidones de 20 litros.',
            'category': cats['Dispensadores'],
            'stock': 100,
            'is_active': True,
        },
        {
            'name': 'Dispenser Eléctrico',
            'price': 35.00,
            'description': 'Dispensador eléctrico para bidones de 20 litros.',
            'category': cats['Dispensadores'],
            'stock': 100,
            'is_active': True,
        },
        {
            'name': 'Dispenser de Mesa (para bidones de 20L)',
            'price': 50.00,
            'description': 'Dispensador manual de mesa, compatible con bidones de 20 litros.',
            'category': cats['Dispensadores'],
            'stock': 100,
            'is_active': True,
        },

        # Compras nuevas
        {
            'name': 'Bidón nuevo de 20L (con agua)',
            'price': 50.00,
            'description': 'Bidón nuevo de 20 litros lleno de agua purificada (envase no retornable).',
            'category': cats['Compras nuevas'],
            'stock': 100,
            'is_active': True,
        },
        {
            'name': 'Bidón nuevo de 10L (con agua)',
            'price': 35.00,
            'description': 'Bidón nuevo de 10 litros lleno de agua purificada (envase no retornable).',
            'category': cats['Compras nuevas'],
            'stock': 100,
            'is_active': True,
        },

        # Accesorios
        {
            'name': 'Grifo para dispenser de mesa',
            'price': 15.00,
            'description': 'Grifo de repuesto para dispensador de mesa.',
            'category': cats['Accesorios'],
            'stock': 100,
            'is_active': True,
        },
    ]

    desired_names = [p['name'] for p in desired]

    # Upsert desired products
    for p in desired:
        prod, created = Product.objects.get_or_create(name=p['name'], defaults={
            'description': p['description'],
            'price': p['price'],
            'stock': p['stock'],
            'is_active': p['is_active'],
        })
        # Update fields to match desired exactly
        prod.description = p['description']
        prod.price = p['price']
        prod.stock = p['stock']
        prod.is_active = p['is_active']
        prod.category = p['category']
        prod.save()

    # Delete products not in desired list
    for prod in Product.objects.all():
        if prod.name not in desired_names:
            # remove explicitly unwanted names listed by user
            if prod.name in ['Botella de Agua 500ml (Pack x6)', '10 Litros de Agua de Mesa Santíago']:
                prod.delete()
            else:
                # delete any product not in desired list per user instruction
                prod.delete()


def reverse_func(apps, schema_editor):
    # No reverse: do not recreate deleted products
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_add_category_and_seed'),
    ]

    operations = [
        migrations.RunPython(finalize_catalog, reverse_func),
    ]
