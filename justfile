_default:
	just --list

check *args:
	uv run ruff check --exclude proto {{args}}

fmt *args:
	uv run ruff format --exclude proto {{args}}

compile:
	uv run python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/rollercoaster.proto
