# FROM debian:buster-slim as base
FROM python:3.11-slim as base

# # If this is set to a non-empty string, Python won’t try
# # to write .pyc files on the import of source modules
ENV PYTHONDONTWRITEBYTECODE=1

# # Force the stdout and stderr streams to be unbuffered.
# # This option has no effect on the stdin stream.
ENV PYTHONUNBUFFERED=1

# Create Group: conda
RUN groupadd -r conda --gid 900

# Instalacao Miniconda
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    procps \
    gcc \
    ca-certificates \
    wget \
    python3-dev \
    build-essential \
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

# Set environment variable to automatically accept conda TOS
ENV CONDA_ALWAYS_YES=true
ENV CONDA_AUTO_ACTIVATE_BASE=false

# Accept conda terms of service using exact commands from error message
RUN /opt/conda/bin/conda config --set always_yes true && \
    /opt/conda/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    /opt/conda/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r && \
    /opt/conda/bin/conda config --set channel_priority flexible && \
    /opt/conda/bin/conda update -n base -c defaults conda && \
    /opt/conda/bin/conda env create -f environment.yml

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
ARG USERNAME=orch
ARG USERID=1000
ARG GROUPID=1000
ARG BASEDIR=/app

ENV BASE_DIR ${BASEDIR}
ENV LOG_DIR ${LOG_DIR}

RUN mkdir -p ${BASE_DIR}

# Copy app files into container
WORKDIR $BASE_DIR
COPY . $BASE_DIR

RUN mkdir -p ${BASE_DIR}/django_static \
    ${BASE_DIR}/django_static/rest_framework \
    ${BASE_DIR}/django_static/admin \
    ${BASE_DIR}/core/migrations \
    && chmod -R g+w ${BASE_DIR}

# Create group
RUN groupadd --gid ${GROUPID} $USERNAME

# Create user
RUN useradd --uid ${USERID} --gid ${GROUPID} --shell /bin/bash --create-home ${USERNAME}
RUN usermod -a -G ${GROUPID},900 ${USERNAME}
RUN chown -R ${USERID}:${GROUPID} ${BASE_DIR}

COPY --chmod=0775 ./sh/entrypoint.sh /entrypoint.sh

# Switch to non-priviliged user and run app
USER $USERNAME
RUN /bin/bash --login -c "conda init bash \
    && echo 'source ${BASE_DIR}/sh/env.sh' >> ~/.bashrc \
    && source ~/.bashrc"

ENTRYPOINT [ "/entrypoint.sh" ]
