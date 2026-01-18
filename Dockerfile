FROM python:3.12-alpine
RUN apk add --no-cache gcc musl-dev libffi-dev postgresql-dev build-essential
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "run.py"]