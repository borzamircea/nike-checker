FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy

# Install only what's needed
RUN apt-get update && apt-get install -y \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY checker.py .

# Persistent profile
RUN mkdir -p /app/profile

ENV DISPLAY=:99

CMD ["bash", "-c", "rm -f /tmp/.X99-lock && Xvfb :99 -screen 0 1280x800x24 & python checker.py"]