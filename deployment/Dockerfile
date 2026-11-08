# Self-contained, private, one-backend operator service. No production signer.
FROM python:3.12.12-slim-bookworm
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends openssl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 10001 hamapp \
    && useradd -u 10001 -g 10001 -M -s /usr/sbin/nologin hamapp \
    && install -d -o hamapp -g hamapp -m 0700 /data
WORKDIR /opt/hamapp
COPY --chown=10001:10001 scripts/ /opt/hamapp/scripts/
USER 10001:10001
ENTRYPOINT ["python", "-B", "/opt/hamapp/scripts/hamapp_operator.py"]
CMD ["start", "--root", "/data/service"]
