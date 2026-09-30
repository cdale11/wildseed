FROM python:3.13-slim
WORKDIR /app
RUN useradd --create-home --uid 10001 wildseed
COPY wildseed ./wildseed
COPY web ./web
RUN mkdir /app/data && chown wildseed:wildseed /app/data
USER wildseed
EXPOSE 8080
CMD ["python", "-m", "wildseed.server", "--host", "0.0.0.0", "--workers", "0"]
