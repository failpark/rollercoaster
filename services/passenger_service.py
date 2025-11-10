import grpc
from google.protobuf import empty_pb2

from proto import rollercoaster_pb2, rollercoaster_pb2_grpc
from services.base import BaseService


class PassengerService(BaseService, rollercoaster_pb2_grpc.passengerServicer):
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
		self.passenger_id: int | None = None
		self.is_on_ride = False

	def _configure_server(self, server: grpc.Server) -> None:
		rollercoaster_pb2_grpc.add_passengerServicer_to_server(self, server)

	def register_with_rollercoaster(self) -> bool:
		channel = self.create_channel(self.rollercoaster_host, self.rollercoaster_port)
		stub = rollercoaster_pb2_grpc.rollercoasterStub(channel)
		request = rollercoaster_pb2.RegistrationRequest(host=self.host, port=self.port)
		response = stub.register_passenger(request)
		channel.close()

		if response.success:
			self.passenger_id = response.id
			return True
		return False

	def i_am_boarding(self, request, context) -> empty_pb2.Empty:
		self.is_on_ride = True
		return empty_pb2.Empty()

	def i_am_disembarking(self, request, context) -> empty_pb2.Empty:
		self.is_on_ride = False
		return empty_pb2.Empty()

	def get_status(self) -> dict[str, int | None | bool | str]:
		return {
			'passenger_id': self.passenger_id,
			'is_on_ride': self.is_on_ride,
			'address': self.address,
		}
