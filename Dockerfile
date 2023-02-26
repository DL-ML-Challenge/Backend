FROM python:3.10
WORKDIR /app/
ADD ./requirements.txt ./
RUN pip install -r ./requirements.txt
ADD ./ ./
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["/bin/sh", "-c" , "python manage.py collectstatic --noinput && python manage.py migrate && gunicorn --bind 0.0.0.0:8000 AIChallenge.wsgi"]
