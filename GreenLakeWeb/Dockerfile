FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y ffmpeg
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
