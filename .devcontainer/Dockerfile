FROM mcr.microsoft.com/devcontainers/python:0-3.11

# If this is set to a non-empty string, Python won’t try
# to write .pyc files on the import of source modules
ENV PYTHONDONTWRITEBYTECODE=1

# Force the stdout and stderr streams to be unbuffered.
# This option has no effect on the stdin stream.
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get -y install --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg2 \
    software-properties-common \
   && curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add - \
   && add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
   && apt-get update \
   && apt-get -y install --no-install-recommends docker-ce \
   # Clean up
   && apt-get autoremove -y \
   && apt-get clean -y \
   && rm -rf /var/lib/apt/lists/*

# Symlink docker socket
RUN ln -s "/var/run/docker-host.sock" "/var/run/docker.sock"

# [Optional] If your requirements rarely change, uncomment this section to add them to the image.
COPY ./backend/requirements.txt /tmp/pip-tmp/
RUN pip install --upgrade pip wheel setuptools \
    && pip --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp

ENV BASE_DIR=/app
COPY --chmod=0775 ./backend/sh/entrypoint.sh /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]