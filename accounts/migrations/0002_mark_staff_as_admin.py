from django.db import migrations


def mark_staff_as_admin(apps, schema_editor):
    CustomUser = apps.get_model('accounts', 'CustomUser')
    CustomUser.objects.filter(is_superuser=True).update(role='ADMIN')
    CustomUser.objects.filter(is_staff=True).update(role='ADMIN')


class Migration(migrations.Migration):
    dependencies = [('accounts', '0001_initial')]

    operations = [migrations.RunPython(mark_staff_as_admin, migrations.RunPython.noop)]