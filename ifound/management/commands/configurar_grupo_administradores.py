from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError


GROUP_NAME = 'Administradores do iFound'
PERMISSION_CODENAME = 'access_ifound_admin_area'


class Command(BaseCommand):
    help = 'Cria o grupo de administradores do iFound e associa a permissão de acesso administrativo.'

    def handle(self, *args, **options):
        permission = Permission.objects.filter(
            content_type__app_label='ifound',
            codename=PERMISSION_CODENAME,
        ).first()
        if permission is None:
            raise CommandError(
                'Permissão administrativa ausente. Execute migrate antes deste comando.'
            )

        group, created = Group.objects.get_or_create(name=GROUP_NAME)
        group.permissions.add(permission)

        action = 'Criado' if created else 'Configurado'
        self.stdout.write(
            self.style.SUCCESS(
                f'{action} o grupo "{GROUP_NAME}" com a permissão administrativa do iFound.'
            )
        )
