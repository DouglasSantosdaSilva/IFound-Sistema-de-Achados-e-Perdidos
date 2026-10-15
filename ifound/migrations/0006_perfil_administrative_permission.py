from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ifound', '0005_perfil_foto_image'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='perfil',
            options={
                'permissions': [
                    ('access_ifound_admin_area', 'Can access the iFound administrative area'),
                ],
            },
        ),
    ]
