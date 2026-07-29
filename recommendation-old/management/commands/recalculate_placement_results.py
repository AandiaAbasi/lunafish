from django.core.management.base import BaseCommand

from recommendation.models import StudentTestResponse
from recommendation.utils import calculate_test_result


class Command(BaseCommand):
    help = 'Recalculate completed English placement results using CEFR summary logic.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--response-id',
            type=int,
            help='Recalculate only one StudentTestResponse.',
        )

    def handle(self, *args, **options):
        queryset = StudentTestResponse.objects.filter(status='completed').select_related('test', 'user')

        response_id = options.get('response_id')
        if response_id:
            queryset = queryset.filter(id=response_id)

        success = 0
        failed = 0

        for response in queryset.iterator():
            try:
                calculate_test_result(response)
                success += 1
            except Exception as exc:
                failed += 1
                self.stderr.write(
                    self.style.ERROR(
                        f'Response {response.id}: {exc}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Recalculated: {success}; failed: {failed}'
            )
        )
