import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load the right env file early
env_file = os.environ.get('DJANGO_ENV_FILE', BASE_DIR / 'dev.env')
load_dotenv(dotenv_path=env_file)

# Now load settings dynamically
DJANGO_ENV = os.getenv("DJANGO_ENV", "dev")

if DJANGO_ENV == "prod":
    from .prod import *
elif DJANGO_ENV == "dev":
    from .dev import *
else:
    raise ValueError(f"Unknown DJANGO_ENV: {DJANGO_ENV}")