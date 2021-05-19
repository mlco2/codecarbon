FROM ubuntu:20.04

RUN apt-get update \
    && apt update -y \
    && apt-get upgrade -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    curl \
    nodejs \
    npm \
    sudo \

    && rm -rf /var/lib/apt/lists/*
