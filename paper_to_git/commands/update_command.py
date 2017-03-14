"""
"""

from paper_to_git.commands.base import BaseCommand
from paper_to_git.models import PaperDoc


__all__ = [
    'UpdateCommand',
    ]


class UpdateCommand(BaseCommand):
    """Pull the list of Paper docs and update the database."""

    name = 'update'

    def add(self, parser, command_parser):
        self.parser = parser

    def process(self, args):
        print("Pulling the list of paper docs...")
        for doc in PaperDoc.get_docs():
            print(doc)
