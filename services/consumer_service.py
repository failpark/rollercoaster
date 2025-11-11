import random
import threading

from services.base import BaseService


class ConsumerService(BaseService):
	def __init__(
		self,
		host: str,
		port: int,
		rollercoaster_host: str = 'localhost',
		rollercoaster_port: int = 50051,
	) -> None:
		super().__init__(host, port)
		self.rollercoaster_host = rollercoaster_host
		self.rollercoaster_port = rollercoaster_port
		self._shutdown_timer: threading.Timer | None = None

	def delayed_retry(self) -> None:
		delay = random.uniform(3.0, 7.0)
		print(f're-registering in {delay:.1f} seconds...')
		self._shutdown_timer = threading.Timer(delay, self.register_with_rollercoaster)
		self._shutdown_timer.start()

	def delayed_shutdown(self) -> None:
		print('shutting down ...')
		threading.Timer(2.0, self.stop_server).start()

	def register_with_rollercoaster(self) -> bool: ...