FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src

# Dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    curl \
    libpq-dev \
    pkg-config \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Instala o UV (instalador de pacotes ultrarrápido)
ADD https://astral.sh/uv/install.sh /uv-installer.sh

RUN sh /uv-installer.sh && rm /uv-installer.sh

# Adiciona o uv ao PATH
ENV PATH="/root/.local/bin/:$PATH"

# Copia os requisitos do Python
COPY pyproject.toml .

# Instala as dependências com o UV
RUN uv pip install . --system --no-build-isolation

# Copia o restante da aplicação
COPY . /usr/src

RUN python3 manage.py collectstatic --noinput --clear

EXPOSE 80

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:80", "--timeout", "60"]
