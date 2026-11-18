FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.lock pyproject.toml README.md LICENSE ./
COPY src ./src
COPY tests ./tests
COPY examples ./examples
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.lock \
    && python -m pip install --no-deps .
RUN python -m unittest discover -s tests -v
RUN rata-tools --version

USER 10001
CMD ["rata-tools", "demo", "--observed", "0.91"]
