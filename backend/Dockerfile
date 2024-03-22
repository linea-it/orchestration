# FROM debian:buster-slim as base
FROM python:3.11-slim as base

# # If this is set to a non-empty string, Python won’t try
# # to write .pyc files on the import of source modules
ENV PYTHONDONTWRITEBYTECODE=1

# # Force the stdout and stderr streams to be unbuffered.
# # This option has no effect on the stdin stream.
ENV PYTHONUNBUFFERED=1

# Create Groups: photoz and conda
# Grupo photoz existe no ambiente do linea
RUN groupadd -r photoz --gid 15013 \
    && groupadd -r conda --gid 900

# Instalacao Miniconda
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    procps \
    gcc \
    ca-certificates \
    wget \
    python3-dev \
    build-essential \
    # build-base \
    libpcre3 \
    libpcre3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/conda \
    && wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /opt/conda/miniconda.sh \
    && bash /opt/conda/miniconda.sh -b -u -p /opt/conda \
    && rm -rf /opt/conda/miniconda.sh \
    && /opt/conda/bin/conda init bash \
    && find /opt/conda/ -follow -type f -name '*.a' -delete \
    && find /opt/conda/ -follow -type f -name '*.js.map' -delete \
    && /opt/conda/bin/conda clean -afy \
    && chmod =2775 /opt/conda \
    && ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh

ENV PATH /opt/conda/bin:$PATH

#-------------- Python 3.11 Environment Stage --------------
FROM base as env_base
COPY ./environment.yml .
RUN /bin/bash --login -c "conda init bash \
    && source ~/.bashrc \
    && conda env create -f environment.yml \
    && conda activate orchestration"

# RUN conda install -c conda-forge uwsgi

# Install python packages
COPY ./requirements.txt /tmp/pip-tmp/
RUN /bin/bash --login -c "source /opt/conda/bin/activate \
    && conda activate orchestration \
    && pip install --upgrade pip wheel setuptools \
    && pip --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp"

FROM base

# Python 3.11 environment
COPY --chown=:conda --chmod=775 --from=env_base /opt/conda/envs/orchestration /opt/conda/envs/orchestration

# add user so we can run things as non-root
# https://code.visualstudio.com/remote/advancedcontainers/add-nonroot-user
ARG USERNAME=app
ARG USERID=1000
ARG GROUPID=1000

RUN groupadd --gid ${GROUPID} $USERNAME \
    && useradd --uid ${USERID} --gid ${GROUPID} --shell /bin/bash --create-home ${USERNAME} \
    && usermod -a -G 900 ${USERNAME} \
    && mkdir -p /app \
    && chown -R ${USERID}:${GROUPID} /app 

# RUN /bin/bash --login -c "conda init bash \
#     && source ~/.bashrc \
#     && conda activate orchestration"

# Copy app files into container
WORKDIR /app
COPY . /app

COPY --chmod=0775 ./sh/entrypoint.sh /entrypoint.sh
COPY --chmod=0775 ./sh/start.sh /start.sh
COPY --chmod=0775 ./sh/local_worker.sh /local_worker.sh
COPY --chmod=0775 ./sh/slurm_worker.sh /slurm_worker.sh
COPY --chmod=0775 ./sh/flower.sh /flower.sh

# Switch to non-priviliged user and run app
USER $USERNAME
RUN /bin/bash --login -c "conda init bash \
    && echo 'source /app/sh/env.sh' >> ~/.bashrc \
    && source ~/.bashrc"

ENTRYPOINT [ "/entrypoint.sh" ]
