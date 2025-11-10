_default:
	just --list

start:
	npm run server

run *path:
	npm run client "{{path}}"

run-go:
	go run client/main.go

run-python *path:
	uv run client.py {{path}}

compile-go:
	protoc --go_out=. --go_opt=paths=source_relative --go-grpc_opt=paths=source_relative --go-grpc_out=. proto/fileservice.proto

compile-python:
	uv run python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/rollercoaster.proto
