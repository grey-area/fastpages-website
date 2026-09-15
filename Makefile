help:
	cat Makefile

# start (or restart) the services
server: .FORCE
	docker-compose down --remove-orphans || true;
	docker-compose up

# start (or restart) the services in detached mode
server-detached: .FORCE
	docker-compose down || true;
	docker-compose up -d

# rebuild the services from scratch. Both services now run stock images
# (python:3.12-slim and ruby:3.2), so there is nothing of ours to build.
build: .FORCE
	docker-compose stop || true; docker-compose rm || true;
	docker-compose pull

# convert notebooks to posts without starting Jekyll
convert: .FORCE
	docker-compose up converter

# stop all containers
stop: .FORCE
	docker-compose stop
	docker ps | grep fastpages | awk '{print $1}' | xargs docker stop

# remove all containers
remove: .FORCE
	docker-compose stop  || true; docker-compose rm || true;

# get shell inside the notebook converter service (Must already be running)
bash-nb: .FORCE
	docker-compose exec watcher /bin/bash

# run the converter directly, no Docker (needs the pins in requirements.txt)
convert-local: .FORCE
	python3 -m pip install -r _action_files/requirements.txt
	python3 _action_files/nb2post.py

# get shell inside jekyll service (Must already be running)
bash-jekyll: .FORCE
	docker-compose exec jekyll /bin/bash

# restart just the Jekyll server
restart-jekyll: .FORCE
	docker-compose restart jekyll

.FORCE:
