export MOODLE_BASE_URL := 'http://localhost:8000'
export MOODLE_TOKEN := '519d3ee448bc9ee4d4d96a7ba7edf64a'

help *ARGS:
	@uv run mdl {{ARGS}} --help

show-course:
	uv run mdl courses
	uv run mdl contents 2
	uv run mdl module 2

test:
	@uv run mdl test
