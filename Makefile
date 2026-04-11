IMAGE_NAME:=langgraph-example:main

default:
	@cat ./Makefile
install-deps:
	 @pip3 install -r requirements.txt
image:
	 docker build -t $(IMAGE_NAME) .
run:
	 @docker run -p 8080:8080 -it $(IMAGE_NAME)
run-shell:
	 @docker run -it $(IMAGE_NAME) /bin/bash
exec-shell:
	docker exec -it `docker ps | grep $(IMAGE_NAME) | awk '{print $$1}'` /bin/bash
all: check image
up: all run
check:
	 @pytest -s
clean:
	@find . -name build-info.json | xargs rm -f
	@find . -name server.key | xargs rm -f
	@find . -name server.crt | xargs rm -f
	@find . -name *.log| xargs rm -f
