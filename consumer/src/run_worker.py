from config.settings import AppConfig
from worker.base import Consumer
from models.enums import WorkerType
from models.misc import get_console_handler, date_time_now_utc
import logging
import time


def main(cfg: AppConfig):

    start = time.perf_counter()
    # BookingWorker
    booking_worker = Consumer(
        cfg, WorkerType.BOOKING, cfg.queue_name[1], cfg.queue_name[1]
    )

    # SearchWorker
    search_worker = Consumer(
        cfg, WorkerType.SEARCH, cfg.queue_name[0], cfg.queue_name[0]
    )

    # Start processes
    booking_worker.start()
    search_worker.start()

    end = time.perf_counter()

    end = time.perf_counter()

    cfg.logger.info(
        f"Started processes: {booking_worker.pid}, {search_worker.pid} in {end - start:.4f} seconds. {date_time_now_utc()}"
    )
    # Wait for both to finish
    booking_worker.join()
    search_worker.join()


if __name__ == "__main__":
    cfg = AppConfig()
    # Set up logging
    logging.basicConfig(
        level=cfg.log_level,
        handlers=[
            get_console_handler(),
        ],
    )
    main(cfg)
