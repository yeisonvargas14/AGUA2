import os
import django
import sys

# Ensure project path is on sys.path
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'purificadora.settings')
django.setup()

from products.models import Product

desired = [
    'Botella de Agua 600ml (Pack x9)',
    'Bidón de Agua Purificada 10L (solo agua)',
    'Sachet de Agua 250ml (Paquete de 20)',
    'Botella de 6 litros',
    'Bidón de Agua Purificada 20L (retornable)',
    'Dispenser de Agua Manual',
    'Dispenser Eléctrico',
    'Dispenser de Mesa (para bidones de 20L)',
    'Bidón nuevo de 20L (con agua)',
    'Bidón nuevo de 10L (con agua)',
    'Grifo para dispenser de mesa',
]

others = Product.objects.exclude(name__in=desired)
print('Will deactivate', others.count(), 'products')
others.update(is_active=False)
print('Done. Active products:')
print(list(Product.objects.filter(is_active=True).values_list('name', flat=True)))
