FROM python:3.8
WORKDIR /app/
ADD ./requirements.txt ./
RUN echo "[global]\n\
index-url = https://pypi.iranrepo.ir/simple" > /root/.pip/pip.conf
RUN pip install -r ./requirements.txt
ADD ./ ./
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["/bin/sh", "-c" , "python manage.py collectstatic --noinput && python manage.py migrate && gunicorn --bind 0.0.0.0:8000 AIChallenge.wsgi"]
