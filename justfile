start := '49152'
end := '65535'

_default:
	just --list

check *args:
	uv run ruff check --exclude proto {{args}}

fmt *args:
	uv run ruff format --exclude proto {{args}}

compile:
	uv run python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. --mypy_out=. proto/rollercoaster.proto

start:
	uv run main.py rollercoaster 50051

start-passenger *port='0':
	uv run main.py passenger "$(({{start}}+{{port}}))"

start-wagon *port='0':
	uv run main.py wagon  "$(({{end}}-{{port}}))"