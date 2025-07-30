from collections.abc import Callable
import pika
from worker.src.config.settings import AppConfig
from pika.adapters.blocking_connection import BlockingChannel


class Queue:

    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.channel: BlockingChannel | None = None

    def create_exchange(
        self, queue_name: str, exchange_name: str, exchange_type: str, key: str
    ):
        try:
            print("Connecting...")
            connection_params = pika.URLParameters(self.cfg.amqp_url)
            connection = pika.BlockingConnection(connection_params)
            self.channel = connection.channel()
            # accept only one unack-ed message at a time
            self.channel.basic_qos(prefetch_count=1)
            self.channel.queue_declare(queue=queue_name, durable=True)
            self.channel.exchange_declare(
                exchange=exchange_name, exchange_type=exchange_type, passive=True
            )
            self.channel.queue_bind(
                queue=queue_name, exchange=exchange_name, routing_key=key
            )
        except Exception as e:
            print(e)

    def listen_to_queue(self, queue_name: str, call_back: Callable) -> None:
        try:
            if not self.channel:
                raise Exception("Connection is not established.")
            self.channel.basic_consume(queue_name, call_back)
            # method_frame, properties, body = self.channel.basic_get(queue_name)
            self.channel.start_consuming()
            print(" [*] Worker Waiting for JOB.")
        except Exception as e:
            print(f"+] Consumer Exception: {e}")

    def send_message(self, exchange_name: str, key: str, message: str) -> None:
        try:
            if not self.channel:
                raise Exception("Connection is not established.")
            self.channel.basic_publish(
                exchange_name,
                key,
                body=message.encode(),
                properties=pika.BasicProperties(
                    delivery_mode=pika.DeliveryMode.Persistent
                ),
            )
        except Exception as e:
            print(f"+] Publisher Exception: {e}")
