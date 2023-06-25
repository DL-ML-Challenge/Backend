import json

import gdown
import pika
from django.conf import settings

from challenge.models import GroupSubmit


def send_submit_to_judge(submit: GroupSubmit):
    if submit.phase.challenge.name == "ml":
        return
    credentials = pika.PlainCredentials(settings.RABBITMQ_USERNAME, settings.RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(settings.RABBITMQ_ENDPOINT, 5672, '/', credentials)
    with pika.BlockingConnection(parameters) as connection, connection.channel() as channel:
        channel.exchange_declare('challenge', exchange_type='fanout')
        channel.queue_declare(queue='submit')
        channel.queue_bind(exchange='challenge', queue='submit')
        channel.basic_publish(
            exchange='challenge',
            routing_key='',
            body=json.dumps(
                {
                    'phase': submit.phase.name,
                    'tag': submit.phase.tag,
                    'student_number': submit.student_code,
                    'file_id': submit.id,
                    'file_name': submit.file.name.rsplit(".", 1)[0].split("/", 1)[1],
                }
            ).encode()
        )


def download_from_drive(tmp_file: str, url: str):
    output = gdown.download(
        url=url,
        output=tmp_file,
        quiet=True,
        fuzzy=True,
    )
    return output is not None
