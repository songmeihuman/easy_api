worker:
	python -m celery -A easy_api worker -c 1 -l info
