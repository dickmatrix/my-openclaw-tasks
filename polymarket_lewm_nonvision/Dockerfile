FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/workspace/src

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl tini build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 10001 app && useradd --uid 10001 --gid 10001 --create-home --shell /bin/bash app

WORKDIR /workspace

COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip && pip install -r /tmp/requirements.txt

COPY --chown=app:app src /workspace/src
COPY --chown=app:app vendor /workspace/vendor
COPY --chown=app:app selfcheck.py /workspace/selfcheck.py
COPY --chown=app:app run.py /workspace/run.py

RUN mkdir -p /workspace/input /workspace/output /workspace/data /workspace/weights && \
    chown -R app:app /workspace

USER app
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "/workspace/selfcheck.py"]
