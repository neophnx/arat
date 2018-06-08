tests2: clean
	python2 -m nose -v --with-coverage --with-doctest --cover-package server,standalone tests standalone.py server

tests3: clean
	python3 -m nose -v --with-coverage --with-doctest --cover-package server,standalone tests standalone.py server

lint2:
	autopep8 -i $(DOC)
	python2 -m pylint $(DOC)
	
lint-all:
	autopep8 -j=-1 -ir standalone.py server tests
	python3 -m pylint standalone.py server tests |tee pylint.txt

static-test:
	python3 -m pylint -j8 --errors-only standalone.py server tests |tee pylint.txt
    

clean:
	find . -name "*.pyc" | xargs rm -f
	find data -name ".stats_cache" |xargs rm -f
	rm -rf work/*
	rm -rf pylint.txt .coverage

test-platform:
	docker build -f tests-docker/Dockerfile-ubuntu_18.04-CPython_2.7 -t ubuntu_18.04-cpython_2.7 .
	docker run ubuntu_18.04-cpython_2.7 2> tests-docker/ubuntu_18.04-CPython_2.7.txt
	
	tail tests-docker/ubuntu_18.04-CPython_2.7.txt
    
	docker build -f tests-docker/Dockerfile-ubuntu_18.04-CPython_3.6 -t ubuntu_18.04-cpython_3.6 .
	docker run ubuntu_18.04-cpython_3.6 2> tests-docker/ubuntu_18.04-CPython_3.6.txt

	tail tests-docker/ubuntu_18.04-CPython_3.6.txt
	
