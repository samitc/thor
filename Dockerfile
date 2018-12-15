FROM python:3.7-alpine3.8
RUN addgroup -g 9999 -S app && adduser -S -u 9999 -G app app
COPY --chown=app ./*.py /app/
WORKDIR /app
VOLUME /app
USER app
ENTRYPOINT ["python"]
