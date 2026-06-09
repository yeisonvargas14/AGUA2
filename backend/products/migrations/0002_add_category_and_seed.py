from django.db import migrations, models
import datetime


def create_categories_and_products(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    Product = apps.get_model('products', 'Product')
    # Create categories
    cat_names = ['Productos', 'Dispensadores', 'Compras nuevas', 'Accesorios']
    cats = {}
    for name in cat_names:
        obj, _ = Category.objects.get_or_create(name=name)
        cats[name] = obj

    # Helper to create or update products
    def upsert(name, defaults):
        prod, created = Product.objects.get_or_create(name=name, defaults=defaults)
        if not created:
            for k, v in defaults.items():
                setattr(prod, k, v)
        prod.save()
        return prod

    # 1. Correct / update existing
    upsert('Botella de Agua 600ml (Pack x9)', {
        'price': 35.00,
        'description': 'Paquete de 9 botellas de agua purificada de 600ml, ideal para hidratación diaria.',
        'stock': 0,
        'category': cats['Productos']
    })

    # Dispenser Manual - try to find variants
    disp_manual = Product.objects.filter(name__icontains='Dispens').first()
    if disp_manual:
        disp_manual.category = cats['Dispensadores']
        disp_manual.save()

    # Bidón de Agua 10L - update description and price
    bidon_10 = Product.objects.filter(name__icontains='10L').first()
    if bidon_10:
        bidon_10.description = 'Bidón mediano de agua purificada.'
        bidon_10.price = 5.00
        bidon_10.category = cats['Productos']
        bidon_10.save()

    # 2. Add new products
    upsert('Sachet de Agua 250ml (Paquete de 20)', {
        'price': 10.00,
        'description': 'Paquete de 20 sachets de 250ml de agua purificada.',
        'stock': 0,
        'category': cats['Productos']
    })

    upsert('Dispenser Eléctrico', {
        'price': 35.00,
        'description': 'Dispensor eléctrico compatible con bidones estándar.',
        'stock': 0,
        'category': cats['Dispensadores']
    })

    upsert('Botella de 6 litros', {
        'price': 10.00,
        'description': 'Botella de 6 litros de agua purificada.',
        'stock': 0,
        'category': cats['Productos']
    })

    upsert('Dispenser de Mesa (para bidones de 20L)', {
        'price': 50.00,
        'description': 'Dispenser de mesa compatible con bidones de 20 litros.',
        'stock': 0,
        'category': cats['Dispensadores']
    })

    # 5. Compras nuevas - bidones no retornables
    upsert('Bidón nuevo de 20L (con agua)', {
        'price': 50.00,
        'description': 'Bidón nuevo de 20 litros lleno de agua purificada (envase no retornable).',
        'stock': 0,
        'category': cats['Compras nuevas']
    })

    upsert('Bidón nuevo de 10L (con agua)', {
        'price': 35.00,
        'description': 'Bidón nuevo de 10 litros lleno de agua purificada (envase no retornable).',
        'stock': 0,
        'category': cats['Compras nuevas']
    })

    # 6. Accessories
    upsert('Grifo para dispenser de mesa', {
        'price': 15.00,
        'description': 'Grifo de repuesto para dispenser de mesa.',
        'stock': 0,
        'category': cats['Accesorios']
    })


def reverse_func(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    Product = apps.get_model('products', 'Product')
    # Do not delete products; only remove categories created here if empty
    for name in ['Productos', 'Dispensadores', 'Compras nuevas', 'Accesorios']:
        try:
            cat = Category.objects.get(name=name)
            # only delete if no products
            if cat.products.count() == 0:
                cat.delete()
        except Category.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='products', to='products.category'),
        ),
        migrations.RunPython(create_categories_and_products, reverse_func),
    ]
