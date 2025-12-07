# Dockerfile

# Use Ubuntu to install Python and uv
# For production, you could use python:3.11-slim

FROM ubuntu:22.04@sha256:3c61d3759c2639d4b836d32a2d3c83fa0214e36f195a3421018dbaaf79cbe37f

# set work directory
WORKDIR /app
# set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Prevent apt to ask for region
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y software-properties-common curl && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y gcc libpq-dev python3.11 python3.11-dev

RUN ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/bin/python3.11 /usr/bin/python3

# Download the latest UV installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Copy project files
COPY pyproject.toml /app/
COPY codecarbon /app/codecarbon
COPY carbonserver /app/carbonserver

# Install dependencies using uv with the api dependency group
RUN uv pip install --system -e ".[api]"

COPY ./carbonserver/docker/entrypoint.sh /opt
RUN chmod a+x /opt/entrypoint.sh

WORKDIR /app/carbonserver

EXPOSE 8000
ENTRYPOINT ["/opt/entrypoint.sh"]
