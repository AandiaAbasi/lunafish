FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Use Abrha mirror for Debian packages (avoids connectivity issues in Iran)
RUN echo "deb https://repo.abrha.net/debian trixie main contrib non-free non-free-firmware" > /etc/apt/sources.list.d/abrha.list && \
    echo "deb https://repo.abrha.net/debian trixie-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list.d/abrha.list && \
    echo "deb https://repo.abrha.net/debian trixie-backports main contrib non-free non-free-firmware" >> /etc/apt/sources.list.d/abrha.list && \
    echo "deb https://repo.abrha.net/debian-security trixie-security main non-free-firmware" >> /etc/apt/sources.list.d/abrha.list && \
    rm -f /etc/apt/sources.list.d/debian.sources

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    build-essential \
    pkg-config \
    gettext \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -i https://mirror.abrha.net/repository/pypi/simple --trusted-host mirror.abrha.net pysocks && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/staticfiles /app/mediafiles && \
    python manage.py compilemessages 2>/dev/null || true && \
    python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000
CMD ["gunicorn", "fofofish.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "30", "--access-logfile", "-"]
