from __future__ import unicode_literals

from optparse import make_option

from django.apps import app_cache
from django.core.management.base import AppCommand
from django.db import connections, DEFAULT_DB_ALIAS


class Command(AppCommand):
    help = 'Prints the SQL statements for resetting sequences for the given app name(s).'

    option_list = AppCommand.option_list + (
        make_option('--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Nominates a database to print the '
                'SQL for.  Defaults to the "default" database.'),

    )

    output_transaction = True

    def handle_app(self, app, **options):
        connection = connections[options.get('database')]
        return '\n'.join(connection.ops.sequence_reset_sql(self.style, app_cache.get_models(app, include_auto_created=True)))
