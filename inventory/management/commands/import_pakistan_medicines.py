import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from inventory.models import MedicineReference


def decimal_or_none(value):
    cleaned = str(value or '').replace(',', '').replace('Rs.', '').replace('PKR', '').strip()
    if not cleaned or cleaned.lower() in {'nan', 'none', 'null'}:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


class Command(BaseCommand):
    help = 'Imports Pakistan medicine reference data from a CSV file.'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str)
        parser.add_argument('--clear', action='store_true', help='Clear existing reference records before import.')

    @transaction.atomic
    def handle(self, *args, **options):
        csv_path = Path(options['csv_path'])
        if not csv_path.exists():
            raise CommandError(f'CSV file not found: {csv_path}')
        if options['clear']:
            MedicineReference.objects.all().delete()
        created = updated = skipped = 0
        with csv_path.open(encoding='utf-8-sig', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            required_columns = {'name', 'company', 'pack_size', 'link', 'sale_price', 'mrp', 'letter'}
            if not required_columns.issubset(reader.fieldnames or set()):
                raise CommandError('CSV does not contain the expected Pakistan medicine dataset columns.')
            for row in reader:
                name = (row.get('name') or '').strip()
                if not name:
                    skipped += 1
                    continue
                defaults = {
                    'sale_price': decimal_or_none(row.get('sale_price')),
                    'mrp': decimal_or_none(row.get('mrp')),
                    'source_link': (row.get('link') or '').strip(),
                    'letter': (row.get('letter') or '').strip(),
                }
                _, was_created = MedicineReference.objects.update_or_create(
                    name=name,
                    company=(row.get('company') or '').strip(),
                    pack_size=(row.get('pack_size') or '').strip(),
                    defaults=defaults,
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
        self.stdout.write(self.style.SUCCESS(f'Import complete: {created} created, {updated} updated, {skipped} skipped.'))