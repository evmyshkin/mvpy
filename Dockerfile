# ===============================================
# BASE IMAGE: Python 3.13-alpine + uv
# ===============================================
FROM astral/uv:python3.13-alpine AS base-image

ENV UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PROJECT_PATH="/app" \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1

# Создаем пользователя и рабочую директорию
RUN addgroup -g 2000 user && \
    adduser -u 2000 -S user -G user -s /bin/sh -h /home/user && \
    mkdir -p $PROJECT_PATH && chown user:user $PROJECT_PATH

WORKDIR $PROJECT_PATH

# Устанавливаем системные зависимости один раз
RUN apk add --no-cache build-base

COPY pyproject.toml uv.lock ./


# =====================================================
# BUILD (dev)
# =====================================================
FROM base-image AS build-dev-image

RUN uv sync --locked --verbose --no-install-project

COPY . /app

RUN uv sync --locked --verbose



# =====================================================
# IMAGE (dev)
# =====================================================
FROM base-image AS dev-image

ENV PRODUCTION=False

COPY --from=build-dev-image --chown=user:user /app /app

USER user
WORKDIR /app

CMD ["uv", "run", "-m", "app.main"]


# =====================================================
# BUILD (production) без dev-зависимостей
# =====================================================
FROM base-image AS build-production-image

RUN uv sync --locked --no-dev --verbose --no-install-project

COPY . /app

# Удаляем лишние папки (migrations нужны для контейнера migrate)
RUN rm -rf /app/tests \
    && uv sync --locked --no-dev --verbose


# =====================================================
# IMAGE (production) без dev-зависимостей
# =====================================================
FROM base-image AS production-image

ENV PRODUCTION=True \
	PYTHONOPTIMIZE=1

COPY --from=build-production-image --chown=user:user /app /app

USER user
WORKDIR /app

CMD ["uv", "run", "-m", "app.main"]

