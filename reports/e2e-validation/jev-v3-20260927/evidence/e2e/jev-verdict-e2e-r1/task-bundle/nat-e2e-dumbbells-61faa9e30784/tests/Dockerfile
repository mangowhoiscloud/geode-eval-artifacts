FROM python:3.12.12-slim-bookworm@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c
WORKDIR /tests
COPY requirements.txt /tests/requirements.txt
RUN python -m pip install --disable-pip-version-check --no-cache-dir --only-binary=:all: --require-hashes -r /tests/requirements.txt
COPY handoff_runtime.py case.json verify.py test.sh /tests/
RUN chmod 555 /tests/test.sh && python -c "from handoff_runtime import verify_handoff_result"
