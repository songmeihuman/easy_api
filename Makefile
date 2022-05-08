venv:
	python3 -m venv venv

setup: requirements.txt venv
	./venv/bin/python -m pip install -r requirements.txt

start: requirements.txt venv
	./venv/bin/python main.py

worker:
	./venv/bin/python -m celery -A easy_api worker -l info

