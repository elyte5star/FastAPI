from modules.config.settings import AppConfig
from pika import URLParameters, BlockingConnection
from collections.abc import Callable



class Queue:

    def __init__(
        self,
        config: AppConfig,
    ) -> None:
        self.cfg = config

    def create_exchange(
        self, queue_name: str, exchange_name: str, exchange_type: str, key: str
    ):
        try:
            connection_params = URLParameters(self.cfg.amqp_url)
            connection = BlockingConnection(connection_params)
            self.channel = connection.channel()
            self.channel.queue_declare(queue=queue_name, durable=True)
            self.channel.exchange_declare(
                exchange=exchange_name, exchange_type=exchange_type
            )
            self.channel.queue_bind(
                queue=queue_name, exchange=exchange_type, routing_key=key
            )
            # accept only one unack-ed message at a time
            self.channel.basic_qos(prefetch_count=1)
            print(" [*] Worker Waiting for JOB.")
        except Exception as e:
            print(e)

    def listen_to_queue(self, queue_name: str, call_back: Callable) -> None:
        try:
            self.channel.basic_consume(queue_name, call_back)
            self.channel.start_consuming()
        except Exception as e:
            print(f"+] Consumer Exception: {e}")

    def send_message(self, exchange_name: str, key: str, message: str) -> None:
        try:
            self.channel.basic_publish(exchange_name, key, body=message.encode())
        except Exception as e:
            print(f"+] Publisher Exception: {e}")


config = AppConfig()

q = Queue(config=config)

q.create_exchange("BOOKING", "", "", "BOOKING")
