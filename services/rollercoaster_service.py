import threading
import time

import grpc
from google.protobuf import empty_pb2

from proto import rollercoaster_pb2, rollercoaster_pb2_grpc
from services.base import BaseService


class RollercoasterService(BaseService, rollercoaster_pb2_grpc.rollercoasterServicer):
	def __init__(self, host: str = '0.0.0.0', port: int = 50051) -> None:
		super().__init__(host, port)
		self._wagons: dict[int, tuple[str, int]] = {}
		self._passengers: dict[int, tuple[str, int]] = {}
		self._waiting_wagons: list[int] = []
		self._waiting_passengers: list[int] = []
		self._next_wagon_id = 1
		self._next_passenger_id = 1
		self._lock = threading.Lock()
		self._ride_thread: threading.Thread | None = None
		self._running = False

	def _configure_server(self, server: grpc.Server) -> None:
		rollercoaster_pb2_grpc.add_rollercoasterServicer_to_server(self, server)
		self._start_ride_coordinator()

	def get_status(self, request, context) -> rollercoaster_pb2.StatusResponse:
		status = rollercoaster_pb2.StatusResponse(
			total_wagons=len(self._wagons),
			total_passengers=len(self._passengers),
			waiting_passengers=len(self._waiting_passengers),
		)
		print(status)
		return status

	def register_wagon(
		self, request, context
	) -> rollercoaster_pb2.RegistrationResponse:
		with self._lock:
			wagon_id = self.get_wagon_id(request)
			self._wagons[wagon_id] = (request.host, request.port)
			self._waiting_wagons.append(wagon_id)
			print(f'Wagon {wagon_id} registered from {request.host}:{request.port}')
			return rollercoaster_pb2.RegistrationResponse(id=wagon_id, success=True)

	def get_next_wid(self):
		self._next_wagon_id += 1
		return self._next_wagon_id - 1

	def get_wagon_id(self, request):
		return next(
			(
				key
				for key, value in self._wagons.items()
				if value == (request.host, request.port)
			),
			self.get_next_wid(),
		)

	def register_passenger(
		self, request, context
	) -> rollercoaster_pb2.RegistrationResponse:
		with self._lock:
			passenger_id = self.get_passenger_id(request)
			self._passengers[passenger_id] = (request.host, request.port)
			self._waiting_passengers.append(passenger_id)
			print(
				f'Passenger {passenger_id} registered from {request.host}:{request.port}'
			)
			return rollercoaster_pb2.RegistrationResponse(id=passenger_id, success=True)

	def get_passenger_id(self, request):
		return next(
			(
				key
				for key, value in self._passengers.items()
				if value == (request.host, request.port)
			),
			self.get_next_pid(),
		)

	def get_next_pid(self):
		self._next_passenger_id += 1
		return self._next_passenger_id - 1

	def call_wagon_stationed(self, wagon_host: str, wagon_port: int) -> None:
		channel = self.create_channel(wagon_host, wagon_port)
		stub = rollercoaster_pb2_grpc.wagonStub(channel)
		print('wagon stationed')
		stub.stationed(empty_pb2.Empty())
		channel.close()

	def call_wagon_depart(
		self, wagon_host: str, wagon_port: int, passenger_ids: list[int]
	) -> None:
		channel = self.create_channel(wagon_host, wagon_port)
		stub = rollercoaster_pb2_grpc.wagonStub(channel)
		passenger_list = rollercoaster_pb2.passenger_list(passenger_id=passenger_ids)
		print('wagon depart')
		stub.depart(passenger_list)
		channel.close()

	def call_wagon_arrive(self, wagon_host: str, wagon_port: int) -> None:
		channel = self.create_channel(wagon_host, wagon_port)
		stub = rollercoaster_pb2_grpc.wagonStub(channel)
		print('wagon arrive')
		stub.arrive(empty_pb2.Empty())
		channel.close()

	def call_passenger_boarding(self, passenger_host: str, passenger_port: int) -> None:
		channel = self.create_channel(passenger_host, passenger_port)
		stub = rollercoaster_pb2_grpc.passengerStub(channel)
		print('passenger boarding')
		stub.i_am_boarding(empty_pb2.Empty())
		channel.close()

	def call_passenger_disembarking(
		self, passenger_host: str, passenger_port: int
	) -> None:
		channel = self.create_channel(passenger_host, passenger_port)
		stub = rollercoaster_pb2_grpc.passengerStub(channel)
		print('passenger disembark')
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

	def _start_ride_coordinator(self) -> None:
		self._running = True
		self._ride_thread = threading.Thread(target=self._ride_coordinator, daemon=True)
		self._ride_thread.start()

	def _ride_coordinator(self) -> None:
		print('started coordinating')
		while self._running:
			try:
				with self._lock:
					if (
						len(self._waiting_wagons) >= 1
						and len(self._waiting_passengers) >= 2
					):
						wagon_id = self._waiting_wagons.pop(0)
						wagon_host, wagon_port = self._wagons[wagon_id]

						# Take up to 4 passengers (typical rollercoaster capacity)
						passengers_for_ride = self._waiting_passengers[:4]
						self.remove_waiting_passengers(passengers_for_ride)

						print(
							f'Starting ride: wagon {wagon_id} with passengers {passengers_for_ride}'
						)

						# Release lock before making network calls
						self._coordinate_ride(
							wagon_host, wagon_port, passengers_for_ride
						)

				time.sleep(1)  # Check every second for new rides
			except Exception as e:
				print(f'Ride coordinator error: {e}')

	def _coordinate_ride(
		self, wagon_host: str, wagon_port: int, passenger_ids: list[int]
	) -> None:
		try:
			# 1. Notify wagon it's stationed
			# self.call_wagon_stationed(wagon_host, wagon_port)

			# 2. Notify passengers they're boarding
			for pid in passenger_ids:
				if pid in self._passengers:
					p_host, p_port = self._passengers[pid]
					self.call_passenger_boarding(p_host, p_port)

			# 3. Tell wagon to depart with passengers
			self.call_wagon_depart(wagon_host, wagon_port, passenger_ids)

			# 4. Schedule ride completion handling
			# The wagon's depart() method will handle the ride duration and call arrive()
			# We need to track this ride and handle completion
			threading.Thread(
				target=self._handle_ride_completion,
				args=(wagon_host, wagon_port, passenger_ids),
				daemon=True,
			).start()

		except Exception as e:
			print(f'Ride coordination error: {e}')
			# Return passengers to waiting queue on error
			with self._lock:
				self._waiting_passengers.extend(passenger_ids)

	def _handle_ride_completion(
		self, wagon_host: str, wagon_port: int, passenger_ids: list[int]
	) -> None:
		"""Handle the completion of a ride after wagon signals it's done"""
		try:
			# Wait for the ride to complete (wagon handles the 5 second delay)
			# The wagon will call its own arrive() method, so we wait a bit longer
			print('sleep 7 sek')
			time.sleep(7)  # Wait slightly longer than wagon's ride time

			# Find the wagon ID for this host/port combination
			wagon_id = None
			with self._lock:
				for wid, (host, port) in self._wagons.items():
					if host == wagon_host and port == wagon_port:
						wagon_id = wid
						break

			if wagon_id is not None:
				self.wagon_finished_ride(wagon_id, passenger_ids)

		except Exception as e:
			print(f'Ride completion handling error: {e}')

	def wagon_finished_ride(self, wagon_id: int, passenger_ids: list[int]) -> None:
		"""Called when wagon notifies of ride completion"""
		with self._lock:
			if wagon_id not in self._wagons:
				return

			wagon_host, wagon_port = self._wagons[wagon_id]

			# Notify passengers they're disembarking
			for pid in passenger_ids:
				if pid in self._passengers:
					p_host, p_port = self._passengers[pid]
					self.call_passenger_disembarking(p_host, p_port)

			# Notify wagon of arrival
			self.call_wagon_arrive(wagon_host, wagon_port)

			# Make wagon available again
			self._waiting_wagons.append(wagon_id)
			print(f'Ride completed: wagon {wagon_id} with passengers {passenger_ids}')

	def stop_server(self) -> None:
		self._running = False
		if self._ride_thread:
			self._ride_thread.join(timeout=1)
		super().stop_server()
