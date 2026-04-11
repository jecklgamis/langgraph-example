IMAGE_NAME := langgraph-example:main

.PHONY: install test image run run-shell clean

install:
	pip install -r requirements.txt

test:
	pytest -s

image:
	docker build -t $(IMAGE_NAME) .

run:
	docker run -p 8000:8000 -it $(IMAGE_NAME)

run-shell:
	docker run -it $(IMAGE_NAME) /bin/bash

clean:
	find . -name '__pycache__' -type d | xargs rm -rf
	find . -name '*.pyc' -delete
	find . -name '*.log' -delete
