from django.core.management.base import BaseCommand
from data.models import Instrument


class Command(BaseCommand):
    help = 'Добавляет или обновляет инструмент в БД'

    def add_arguments(self, parser):
        parser.add_argument('--code', type=str, help='Код инструмента (например, EURUSD)')
        parser.add_argument('--name', type=str, help='Название инструмента')
        parser.add_argument('--type', type=str, choices=['FOREX', 'INDEX', 'CRYPTO'], help='Тип инструмента')
        parser.add_argument('--twelvedata-symbol', type=str, help='Символ для TwelveData (например, GDAXI)')
        parser.add_argument('--biquote-symbol', type=str, help='Символ для Biquote (например, DAX)')
        parser.add_argument('--inactive', action='store_true', help='Создать неактивным')

    def handle(self, *args, **options):
        code = options['code'] or self._ask('Код инструмента (например, EURUSD): ')
        name = options['name'] or self._ask('Название инструмента: ')
        instrument_type = options['type'] or self._ask_choice(
            'Тип инструмента', ['FOREX', 'INDEX', 'CRYPTO']
        )
        twelvedata_symbol = options['twelvedata_symbol'] or self._ask(
            f'TwelveData-символ (Enter для "{code}"): ', default=code
        )
        biquote_symbol = options['biquote_symbol'] or self._ask(
            f'Biquote-символ (Enter для "{code}"): ', default=code
        )
        is_active = not options['inactive']

        instrument, created = Instrument.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'instrument_type': instrument_type,
                'twelvedata_symbol': twelvedata_symbol,
                'biquote_symbol': biquote_symbol,
                'is_active': is_active,
            }
        )

        action = 'Создан' if created else 'Обновлён'
        self.stdout.write(self.style.SUCCESS(f'{action} инструмент: {code} ({name})'))
        self.stdout.write(f'   Тип: {instrument_type}')
        self.stdout.write(f'   TwelveData-символ: {twelvedata_symbol}')
        self.stdout.write(f'   Biquote-символ: {biquote_symbol}')
        self.stdout.write(f'   Активен: {is_active}')

    def _ask(self, prompt, default=None):
        value = input(prompt).strip()
        return value if value else default

    def _ask_choice(self, prompt, choices):
        self.stdout.write(f'{prompt}:')
        for i, choice in enumerate(choices, 1):
            self.stdout.write(f'  {i}. {choice}')
        while True:
            value = input('Введите номер: ').strip()
            if value.isdigit() and 1 <= int(value) <= len(choices):
                return choices[int(value) - 1]
            self.stdout.write(self.style.ERROR('Неверный выбор, попробуйте снова.'))