import time

import grpc
from google.protobuf import empty_pb2

from proto import rollercoaster_pb2, rollercoaster_pb2_grpc
from services.consumer_service import ConsumerService


class WagonService(ConsumerService, rollercoaster_pb2_grpc.wagonServicer):
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
		self.wagon_id: int | None = None
		self.current_passengers: list[int] = []

	def _configure_server(self, server: grpc.Server) -> None:
		rollercoaster_pb2_grpc.add_wagonServicer_to_server(self, server)

	def register_with_rollercoaster(self) -> bool:
		channel = self.create_channel(self.rollercoaster_host, self.rollercoaster_port)
		stub = rollercoaster_pb2_grpc.rollercoasterStub(channel)
		request = rollercoaster_pb2.RegistrationRequest(host=self.host, port=self.port)
		response = stub.register_wagon(request)
		channel.close()

		if response.success:
			self.wagon_id = response.id
			print(f'Wagon registered successfully with ID {response.id}')
			return True
		print('Wagon registration failed')
		return False

	def stationed(self, request, context) -> empty_pb2.Empty:
		return empty_pb2.Empty()

	def depart(self, request, context) -> empty_pb2.Empty:
		self.current_passengers = list(request.passenger_id)
		print('Ride takes 5 sek')
		time.sleep(5)
		self._notify_arrival()
		return empty_pb2.Empty()

	def arrive(self, request, context) -> empty_pb2.Empty:
		self.current_passengers = []
		self.delayed_retry()
		return empty_pb2.Empty()

	def _notify_arrival(self) -> None:
		if self.wagon_id is None:
			return

		channel = self.create_channel(self.rollercoaster_host, self.rollercoaster_port)
		try:
			print(f'Wagon {self.wagon_id} ride completed, notifying rollercoaster')
			stub = rollercoaster_pb2_grpc.rollercoasterStub(channel)
			res: rollercoaster_pb2.StatusResponse = stub.get_status(empty_pb2.Empty())
			print(res)

		except Exception as e:
			print(f'Failed to notify rollercoaster of arrival: {e}')
		finally:
			channel.close()
