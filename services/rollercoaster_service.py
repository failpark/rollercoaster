import grpc
from google.protobuf import empty_pb2

from proto import rollercoaster_pb2, rollercoaster_pb2_grpc
from services.base import BaseService


class RollercoasterService(BaseService, rollercoaster_pb2_grpc.rollercoasterServicer):
	def __init__(self, host: str = 'localhost', port: int = 50051) -> None:
		super().__init__(host, port)
		self._wagons: dict[int, tuple[str, int]] = {}
		self._passengers: dict[int, tuple[str, int]] = {}
		self._waiting_wagons: list[int] = []
		self._waiting_passengers: list[int] = []
		self._next_wagon_id = 1
		self._next_passenger_id = 1

	def _configure_server(self, server: grpc.Server) -> None:
		rollercoaster_pb2_grpc.add_rollercoasterServicer_to_server(self, server)

	def get_status(self, request, context) -> rollercoaster_pb2.StatusResponse:
		return rollercoaster_pb2.StatusResponse(
			total_wagons=len(self._wagons),
			total_passengers=len(self._passengers),
			waiting_passengers=len(self._waiting_passengers),
		)

	def register_wagon(
		self, request, context
	) -> rollercoaster_pb2.RegistrationResponse:
		wagon_id = self._next_wagon_id
		self._next_wagon_id += 1
		self._wagons[wagon_id] = (request.host, request.port)
		return rollercoaster_pb2.RegistrationResponse(id=wagon_id, success=True)

	def register_passenger(
		self, request, context
	) -> rollercoaster_pb2.RegistrationResponse:
		passenger_id = self._next_passenger_id
		self._next_passenger_id += 1
		self._passengers[passenger_id] = (request.host, request.port)
		self._waiting_passengers.append(passenger_id)
		return rollercoaster_pb2.RegistrationResponse(id=passenger_id, success=True)

	def call_wagon_stationed(self, wagon_host: str, wagon_port: int) -> None:
		channel = self.create_channel(wagon_host, wagon_port)
		stub = rollercoaster_pb2_grpc.wagonStub(channel)
		stub.stationed(empty_pb2.Empty())
		channel.close()

	def call_wagon_depart(
		self, wagon_host: str, wagon_port: int, passenger_ids: list[int]
	) -> None:
		channel = self.create_channel(wagon_host, wagon_port)
		stub = rollercoaster_pb2_grpc.wagonStub(channel)
		passenger_list = rollercoaster_pb2.passenger_list(passenger_id=passenger_ids)
		stub.depart(passenger_list)
		channel.close()

	def call_wagon_arrive(self, wagon_host: str, wagon_port: int) -> None:
		channel = self.create_channel(wagon_host, wagon_port)
		stub = rollercoaster_pb2_grpc.wagonStub(channel)
		stub.arrive(empty_pb2.Empty())
		channel.close()

	def call_passenger_boarding(self, passenger_host: str, passenger_port: int) -> None:
		channel = self.create_channel(passenger_host, passenger_port)
		stub = rollercoaster_pb2_grpc.passengerStub(channel)
		stub.i_am_boarding(empty_pb2.Empty())
		channel.close()

	def call_passenger_disembarking(
		self, passenger_host: str, passenger_port: int
	) -> None:
		channel = self.create_channel(passenger_host, passenger_port)
		stub = rollercoaster_pb2_grpc.passengerStub(channel)
		stub.i_am_disembarking(empty_pb2.Empty())
		channel.close()

	def get_wagons(self) -> dict[int, tuple[str, int]]:
		return self._wagons.copy()

	def get_passengers(self) -> dict[int, tuple[str, int]]:
		return self._passengers.copy()

	def get_waiting_passengers(self) -> list[int]:
		return self._waiting_passengers.copy()

	def remove_waiting_passengers(self, passenger_ids: list[int]) -> None:
		for pid in passenger_ids:
			if pid in self._waiting_passengers:
				self._waiting_passengers.remove(pid)
