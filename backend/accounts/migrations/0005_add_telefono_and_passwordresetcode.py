from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_driverprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='telefono',
            field=models.CharField(
                blank=True,
                null=True,
                unique=True,
                max_length=20,
                verbose_name='Celular',
                help_text='Número de celular usado para iniciar sesión',
            ),
        ),
        migrations.CreateModel(
            name='PasswordResetCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telefono', models.CharField(max_length=20)),
                ('codigo', models.CharField(max_length=6)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('expira_en', models.DateTimeField()),
                ('usado', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='password_reset_codes', to='accounts.user')),
            ],
            options={
                'verbose_name': 'Código de Recuperación',
                'verbose_name_plural': 'Códigos de Recuperación',
            },
        ),
        migrations.AddIndex(
            model_name='passwordresetcode',
            index=models.Index(fields=['telefono', 'codigo'], name='accounts_prc_telefono_codigo_idx'),
        ),
    ]
