import pika
import json
import os
import logging
from threading import Thread
from merra import download_nc4

def read_file(filename):
    d = None
    with open(filename, 'rb') as f:
        d = f.read()

    return d

def init_rabbitmq(session):

    username = os.environ.get("RMQ_USERNAME")
    password = os.environ.get("RMQ_PASSWORD")
    rmq_host = os.environ.get("RMQ_HOST")

    if not rmq_host:
        rmq_host = 'localhost'

    rmq_port = os.environ.get("RMQ_PORT")

    if not rmq_port:
        rmq_port = 5672

    creds = pika.PlainCredentials(username, password)
    parameters = pika.ConnectionParameters(host=rmq_host, port=rmq_port, credentials=creds)
    connection = pika.BlockingConnection(parameters=parameters)
    channel = connection.channel()
    channel.queue_declare(queue='rpc_queue')


    def send_reply(ch, method, props, data):
        print(f"Reply queue {props.reply_to}")

        content_type = 'application/json' if not props.content_type else props.content_type

        ch.basic_publish(exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(
                content_type = content_type,
                correlation_id = props.correlation_id
                ),
            body=data)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def on_request(ch, method, props, body):

        logging.info(body)

        try:
            data = json.loads(body)
            year = data["year"]
            month = data["month"]
        except json.decoder.JSONDecodeError:
            data = { 'error_message': 'Payload could not be parsed as JSON' }
            return send_reply(ch, method, props, json.dumps(data))
        except KeyError:
            data = { 'error_message': 'Both year and month must be passed' }
            return send_reply(ch, method, props, json.dumps(data))
        except ValueError:
            data = { 'error_message': 'Invalid year,month or plot_type' }
            return send_reply(ch, method, props, json.dumps(data))

        if not (year and month):
            data = { 'error_message': 'Payload must be a string' }
            return send_reply(ch, method, props, data)

        try:
            if "plot_type" in data:
                plot_file = download_nc4(session, year, month, data["plot_type"])
            else:
                plot_file = download_nc4(session, year, month)
        except ValueError:
            data = { 'error_message': 'Invalid year,month or plot_type' }
            return send_reply(ch, method, props, json.dumps(data))


        data = read_file(plot_file)
        props.content_type = 'image/png'
        send_reply(ch, method, props, data)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='rpc_queue', on_message_callback=on_request)

    print(" [x] Awaiting RPC requests")
    thread = Thread(target = channel.start_consuming)
    thread.start()
