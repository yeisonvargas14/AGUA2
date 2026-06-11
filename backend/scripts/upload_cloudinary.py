"""
Script para subir la imagen del dispenser manual a Cloudinary y actualizar la base de datos de productos.
"""
import cloudinary
import cloudinary.uploader
from products.models import Product

cloudinary.config(
    cloud_name='duk0t4y3p',
    api_key='134725759352973',
    api_secret='AlIhRkZEeuPEF3pYd2ulpWH3xK4',
)

# 1. Subir la imagen del Dispenser Manual a Cloudinary
local_image_path = r"C:\Users\Yeison\.gemini\antigravity-ide\brain\f3de2e95-616c-425b-a5d8-4bceb75b4a76\media__1781144220683.png"
print(f"Subiendo {local_image_path} a Cloudinary...")

try:
    result = cloudinary.uploader.upload(
        local_image_path,
        public_id='dispenser_manual',
        folder='products',
        overwrite=True,
        resource_type='image'
    )
    print("Subida exitosa!")
    print("Secure URL:", result['secure_url'])
    print("Public ID:", result['public_id'])
    
    # 2. Actualizar el producto en la base de datos
    # Django-cloudinary-storage espera que asignemos la ruta/nombre relativo del archivo en Cloudinary
    # Generalmente se guarda como 'products/dispenser_manual'
    dispenser_manual = Product.objects.get(id=7)
    dispenser_manual.image = result['public_id']
    dispenser_manual.save()
    print(f"Producto actualizado: {dispenser_manual.name} - Imagen: {dispenser_manual.image}")
    
except Exception as e:
    print("Error al subir o actualizar dispenser manual:", e)

# 3. Configurar el Dispenser Eléctrico con la imagen ya subida
try:
    dispenser_electrico = Product.objects.get(id=12)
    dispenser_electrico.image = 'dispenser_electrico_zkoilm'
    dispenser_electrico.save()
    print(f"Producto actualizado: {dispenser_electrico.name} - Imagen: {dispenser_electrico.image}")
except Exception as e:
    print("Error al actualizar dispenser electrico:", e)
