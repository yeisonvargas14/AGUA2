from django.db import migrations


def create_combo_promotion(apps, schema_editor):
    Promotion = apps.get_model('promotions', 'Promotion')
    Product = apps.get_model('products', 'Product')
    from django.utils import timezone
    # Find products
    try:
        bidon20 = Product.objects.get(name__iexact='Bidón nuevo de 20L (con agua)')
    except Product.DoesNotExist:
        bidon20 = Product.objects.filter(name__icontains='20l').first()

    try:
        dispenser_mesa = Product.objects.get(name__iexact='Dispenser de Mesa (para bidones de 20L)')
    except Product.DoesNotExist:
        dispenser_mesa = Product.objects.filter(name__icontains='Dispenser de Mesa').first()

    if not bidon20 or not dispenser_mesa:
        return

    total = float(bidon20.price) + float(dispenser_mesa.price)
    special_price = 90.00
    if total <= 0:
        discount = 0
    else:
        discount = int(round((1 - (special_price / total)) * 100))
        if discount < 0:
            discount = 0
        if discount > 99:
            discount = 99

    start = timezone.now()
    end = start + timezone.timedelta(days=30)

    promo, created = Promotion.objects.get_or_create(
        name='Pack Familiar: Bidón 20L + Dispenser de Mesa',
        defaults={
            'description': 'Pack promocional: Bidón 20L + Dispenser de Mesa a precio especial.',
            'discount_percentage': discount,
            'start_date': start,
            'end_date': end,
            'is_active': True,
        }
    )
    # ensure products are linked
    promo.products.add(bidon20, dispenser_mesa)
    promo.save()


def reverse_func(apps, schema_editor):
    Promotion = apps.get_model('promotions', 'Promotion')
    Promotion.objects.filter(name='Pack Familiar: Bidón 20L + Dispenser de Mesa').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('promotions', '0001_initial'),
        ('products', '0002_add_category_and_seed'),
    ]

    operations = [
        migrations.RunPython(create_combo_promotion, reverse_func),
    ]
