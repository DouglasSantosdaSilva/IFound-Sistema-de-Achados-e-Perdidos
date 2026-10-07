from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ifound', '0004_remove_item_registrado_por_item_criado_em_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='perfil',
            old_name='foto_url',
            new_name='foto',
        ),
        migrations.AlterField(
            model_name='perfil',
            name='foto',
            field=models.ImageField(blank=True, null=True, upload_to='perfis/'),
        ),
    ]