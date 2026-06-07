FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN python -m compileall /app
CMD ["python", "-m", "classifier_sample"]
