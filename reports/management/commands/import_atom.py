# -*- coding: utf-8 -*-
"""Import Atom feeds with BPD log data."""
import argparse
import logging

from django.core.management.base import BaseCommand

from reports import atom_scraper


class Command(BaseCommand):
    """The Django command."""

    help = 'Import historical data from Atom XML'

    def add_arguments(self, parser):
        """Add optional command arguments."""
        def str2bool(val):
            if val.lower() in ('yes', 'true', 't', 'y', '1'):
                return True
            elif val.lower() in ('no', 'false', 'f', 'n', '0'):
                return False
            else:
                raise argparse.ArgumentTypeError('Boolean value expected.')

        parser.add_argument('--local', type=str2bool, nargs='?',
                            const=True, default='no',
                            help='Import from local data.', dest='local')
        parser.add_argument('--skip-existing', type=str2bool, nargs='?',
                            const=True, default='yes',
                            help='Skip import of existing logs.',
                            dest='skip_existing')
        parser.add_argument('--wipe', type=str2bool, nargs='?',
                            const=True, default='no',
                            help='Wipe existing data before import.',
                            dest='wipe')

    def handle(self, *args, **options):
        """Handle the command."""
        results = atom_scraper.scrape(local=options['local'],
                                      skip_existing=options['skip_existing'],
                                      wipe=options['wipe'],
                                      log_level=logging.DEBUG)
        print 'Total inserted entries {}'.format(results[0])
        print 'Total failed entries {}'.format(results[1])
        print 'Total skipped entries {}'.format(results[2])
