from django.db import migrations


def create_pack_promotion(apps, schema_editor):
    Promotion = apps.get_model('promotions', 'Promotion')
    Product = apps.get_model('products', 'Product')
    from django.utils import timezone

    try:
        bidon = Product.objects.get(name__iexact='Bidón nuevo de 20L (con agua)')
    except Product.DoesNotExist:
        bidon = Product.objects.filter(name__icontains='20l').first()

    try:
        dispenser = Product.objects.get(name__iexact='Dispenser de Mesa (para bidones de 20L)')
    except Product.DoesNotExist:
        dispenser = Product.objects.filter(name__icontains='Dispenser de Mesa').first()

    if not bidon or not dispenser:
        return

    special_price = 90.00
    total = float(bidon.price) + float(dispenser.price)
    discount = 0
    if total > 0:
        discount = int(round((1 - (special_price / total)) * 100))
        if discount < 0:
            discount = 0
        if discount > 99:
            discount = 99

    start = timezone.now()
    end = start + timezone.timedelta(days=30)

    promo, created = Promotion.objects.get_or_create(
        name='Pack Familiar: Bidón 20L nuevo + Dispenser de Mesa',
        defaults={
            'description': 'Pack promocional: Bidón nuevo 20L + Dispenser de Mesa a precio especial.',
            'discount_percentage': discount,
            'start_date': start,
            'end_date': end,
            'is_active': True,
        }
    )
    promo.products.clear()
    promo.products.add(bidon, dispenser)
    promo.save()


def reverse_func(apps, schema_editor):
    Promotion = apps.get_model('promotions', 'Promotion')
    Promotion.objects.filter(name='Pack Familiar: Bidón 20L nuevo + Dispenser de Mesa').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('promotions', '0002_create_combo_promotion'),
        ('products', '0003_finalize_catalog'),
    ]

    operations = [
        migrations.RunPython(create_pack_promotion, reverse_func),
    ]
