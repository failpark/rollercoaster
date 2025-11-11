import sys

from services.consumer_service import ConsumerService
from services.passenger_service import PassengerService
from services.rollercoaster_service import RollercoasterService
from services.wagon_service import WagonService


def create_service(
	service_type: str,
	port: int,
	host: str = '0.0.0.0',
	rollercoaster_host: str = 'localhost',
	rollercoaster_port: int = 50051,
) -> RollercoasterService | WagonService | PassengerService:
	if service_type == 'rollercoaster':
		return RollercoasterService(host, port)
	elif service_type == 'wagon':
		return WagonService(host, port, rollercoaster_host, rollercoaster_port)
	elif service_type == 'passenger':
		return PassengerService(host, port, rollercoaster_host, rollercoaster_port)
	else:
		raise ValueError(f'Unknown service type: {service_type}')


def main() -> None:
	if len(sys.argv) < 3:
		print(
			'Usage: python main.py <service_type> <port> [rollercoaster_host] [rollercoaster_port]'
		)
		print('service_type: rollercoaster, wagon, or passenger')
		sys.exit(1)

	service_type = sys.argv[1]
	host = '0.0.0.0'
	port = int(sys.argv[2])
	rollercoaster_host = str(sys.argv[3]) if len(sys.argv) >= 4 else 'localhost'
	rollercoaster_port = int(sys.argv[4]) if len(sys.argv) == 5 else 50051

	if service_type not in ['rollercoaster', 'wagon', 'passenger']:
		print(f'Unknown service type: {service_type}')
		sys.exit(1)

	service = create_service(
		service_type, port, host, rollercoaster_host, rollercoaster_port
	)
	service.start_server()
	print(f'{service_type} service started on {host}:{port}')

	if (
		isinstance(service, (WagonService | PassengerService))
		and not service.register_with_rollercoaster()
	):
		print(f'Failed to register {service_type}')
		sys.exit(1)

	try:
		service.wait_for_termination()
	except KeyboardInterrupt:
		service.stop_server()


if __name__ == '__main__':
	main()
