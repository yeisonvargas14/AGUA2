"""
Hand-written migration to:
1. Rename existing fields: manager->usuario, name->nombre_empresa, address->direccion,
   latitude->latitud, longitude->longitud, is_active->activa
2. Add new fields: telefono, email_contacto, fecha_creacion, notas_internas, logo
3. Alter the OneToOne field to the new related_name='agencia'
"""
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agencies', '0002_alter_agency_manager'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ---- Renombres de campos existentes ----
        migrations.RenameField(
            model_name='agency',
            old_name='manager',
            new_name='usuario',
        ),
        migrations.RenameField(
            model_name='agency',
            old_name='name',
            new_name='nombre_empresa',
        ),
        migrations.RenameField(
            model_name='agency',
            old_name='address',
            new_name='direccion',
        ),
        migrations.RenameField(
            model_name='agency',
            old_name='latitude',
            new_name='latitud',
        ),
        migrations.RenameField(
            model_name='agency',
            old_name='longitude',
            new_name='longitud',
        ),
        migrations.RenameField(
            model_name='agency',
            old_name='is_active',
            new_name='activa',
        ),

        # ---- Alterar el campo usuario para cambiar related_name y quitar limit_choices_to ----
        migrations.AlterField(
            model_name='agency',
            name='usuario',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='agencia',
                to=settings.AUTH_USER_MODEL,
            ),
        ),

        # ---- Alterar el campo nombre_empresa para max_length=200 ----
        migrations.AlterField(
            model_name='agency',
            name='nombre_empresa',
            field=models.CharField(max_length=200, default=''),
        ),

        # ---- Alterar el campo direccion a TextField ----
        migrations.AlterField(
            model_name='agency',
            name='direccion',
            field=models.TextField(default=''),
        ),

        # ---- Nuevos campos ----
        migrations.AddField(
            model_name='agency',
            name='telefono',
            field=models.CharField(max_length=20, default=''),
        ),
        migrations.AddField(
            model_name='agency',
            name='email_contacto',
            field=models.EmailField(default=''),
        ),
        migrations.AddField(
            model_name='agency',
            name='fecha_creacion',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='agency',
            name='notas_internas',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='agency',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to='logos/'),
        ),
    ]
