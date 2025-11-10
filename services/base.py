from abc import ABC, abstractmethod
from concurrent import futures

import grpc


class BaseService(ABC):
	def __init__(self, host: str, port: int) -> None:
		self.host = host
		self.port = port
		self.server: grpc.Server | None = None

	def start_server(self) -> None:
		if self.server is not None:
			return

		self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
		self._configure_server(self.server)
		self.server.add_insecure_port(f'{self.host}:{self.port}')
		self.server.start()

	def stop_server(self) -> None:
		if self.server is not None:
			self.server.stop(grace=5)
			self.server = None

	def wait_for_termination(self) -> None:
		if self.server is not None:
			self.server.wait_for_termination()

	@abstractmethod
	def _configure_server(self, server: grpc.Server) -> None:
		pass

	def create_channel(self, target_host: str, target_port: int) -> grpc.Channel:
		return grpc.insecure_channel(f'{target_host}:{target_port}')

	@property
	def address(self) -> str:
		return f'{self.host}:{self.port}'
