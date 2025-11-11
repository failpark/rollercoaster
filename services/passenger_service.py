import grpc
from google.protobuf import empty_pb2

from proto import rollercoaster_pb2, rollercoaster_pb2_grpc
from services.consumer_service import ConsumerService


class PassengerService(ConsumerService, rollercoaster_pb2_grpc.passengerServicer):
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
			print(f'Passenger registered successfully with ID {response.id}')
			return True
		print('Passenger registration failed')
		return False

	def i_am_boarding(self, request, context) -> empty_pb2.Empty:
		self.is_on_ride = True
		print('boarding')
		return empty_pb2.Empty()

	def i_am_disembarking(self, request, context) -> empty_pb2.Empty:
		self.is_on_ride = False
		print('disembarking')
		self.delayed_retry()
		return empty_pb2.Empty()

	def get_status(self) -> dict[str, int | None | bool | str]:
		status = {
			'passenger_id': self.passenger_id,
			'is_on_ride': self.is_on_ride,
			'address': self.address,
		}
		print(status)
		return status
