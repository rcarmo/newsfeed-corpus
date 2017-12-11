CHECK_INTERVAL?=5
FETCH_INTERVAL?=15
MONGO_SERVER?=localhost:27017
DATABASE_NAME?=feeds
PORT?=8000

# Run the stack locally
serve:
	docker-compose up --build

# Build the base container when we update dependencies
build:
	docker-compose build

restart-web:
	docker-compose stop web
	docker-compose build web
	docker-compose up -d --no-deps web

repl:
	docker-compose exec web python repl.py

nuke-database:
	docker-compose stop db 
	docker-compose build db
	docker-compose up -d --no-deps db 

# Install deps locally for REPL
host-deps:
	pip install -U -r requirements.txt

clean:
	-rm -f *.pyc
	-docker rm -v $$(docker ps -a -q -f status=exited)
	-docker rmi $$(docker images -q -f dangling=true)
	-docker rmi $$(docker images --format '{{.Repository}}:{{.Tag}}' | grep '$(IMAGE_NAME)')
