import os
import sys
import django
from django.core.management import execute_from_command_line

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.settings")
django.setup()


def main():
    args = sys.argv[1:] or ["runserver"]
    execute_from_command_line(["manage.py"] + args)
