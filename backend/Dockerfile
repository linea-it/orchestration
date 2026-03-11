FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MAMBA_ROOT_PREFIX=/opt/micromamba

RUN groupadd -r mamba --gid 900

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    procps gcc ca-certificates wget bzip2 python3-dev build-essential && \
    apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/micromamba \
    && wget -qO- https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj -C /usr/local/bin --strip-components=1 bin/micromamba && find /opt/micromamba/ -follow -type f -name '*.a' -delete \
    && find /opt/micromamba/ -follow -type f -name '*.js.map' -delete \
    && chmod =2775 /opt/micromamba

ENV PATH /usr/local/bin:/opt/micromamba/bin:$PATH

FROM base as env_base
COPY ./environment.yml .

RUN micromamba create --root-prefix "$MAMBA_ROOT_PREFIX" -y -f environment.yml \
    && micromamba clean --all --yes
COPY ./requirements.txt /tmp/pip-tmp/
RUN micromamba run --root-prefix "$MAMBA_ROOT_PREFIX" -n orchestration pip install --upgrade pip wheel setuptools \
    && micromamba run --root-prefix "$MAMBA_ROOT_PREFIX" -n orchestration pip --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp \
    && micromamba clean --all --yes

FROM base

COPY --chown=:mamba --chmod=775 --from=env_base /opt/micromamba/envs/orchestration /opt/micromamba/envs/orchestration

ARG USERNAME=orch
ARG USERID=1000
ARG GROUPID=1000
ARG BASEDIR=/app

ENV BASE_DIR ${BASEDIR}
ENV LOG_DIR ${LOG_DIR}
ENV PATH /opt/micromamba/envs/orchestration/bin:/usr/local/bin:/opt/micromamba/bin:$PATH

RUN mkdir -p ${BASE_DIR}

WORKDIR $BASE_DIR
COPY . $BASE_DIR

RUN mkdir -p ${BASE_DIR}/django_static \
    ${BASE_DIR}/django_static/rest_framework \
    ${BASE_DIR}/django_static/admin \
    ${BASE_DIR}/core/migrations \
    && chmod -R g+w ${BASE_DIR}

RUN groupadd --gid ${GROUPID} $USERNAME
RUN useradd --uid ${USERID} --gid ${GROUPID} --shell /bin/bash --create-home ${USERNAME}
RUN usermod -a -G ${GROUPID},900 ${USERNAME}
RUN chown -R ${USERID}:${GROUPID} ${BASE_DIR}

COPY --chmod=0775 ./sh/entrypoint.sh /entrypoint.sh

USER $USERNAME
RUN /bin/bash -lc "echo 'source ${BASE_DIR}/sh/env.sh' >> ~/.bashrc"

ENTRYPOINT [ "/entrypoint.sh" ]
