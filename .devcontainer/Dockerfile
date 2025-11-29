# Simple devcontainer Dockerfile for DndCharacter
FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

# Install common tools (git, curl, build essentials). Node/Python provided via devcontainer features.
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    ca-certificates \
    wget \
    unzip \
  && rm -rf /var/lib/apt/lists/*

# Create non-root vscode user (matches Codespaces default)
ARG USER=vscode
ARG UID=1000
ARG GID=1000
RUN groupadd --gid ${GID} ${USER} \
  && useradd -m --uid ${UID} --gid ${GID} ${USER} \
  && mkdir -p /home/${USER}/workspace \
  && chown -R ${USER}:${USER} /home/${USER}

USER ${USER}
WORKDIR /home/${USER}/workspace

CMD ["sleep", "infinity"]
