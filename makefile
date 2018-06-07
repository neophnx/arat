tests2: clean
	python2 -m nose --processes=-1 -v --with-coverage --with-doctest --cover-package server,standalone tests standalone.py server

tests3: clean
	python3 -m nose --processes=-1 -v --with-coverage --with-doctest --cover-package server,standalone tests standalone.py server

lint2:
	autopep8 -i $(DOC)
	python2 -m pylint $(DOC)

clean:
	find . -name "*.pyc" | xargs rm -f
	find data -name ".stats_cache" |xargs rm -f
	rm -rf work/*

test-platform:
	docker build -f tests-docker/Dockerfile-ubuntu_18.04-CPython_2.7 -t ubuntu_18.04-cpython_2.7 .
	docker run ubuntu_18.04-cpython_2.7 2> tests-docker/ubuntu_18.04-CPython_2.7.txt
	
	tail tests-docker/ubuntu_18.04-CPython_2.7.txt
    
	docker build -f tests-docker/Dockerfile-ubuntu_18.04-CPython_3.6 -t ubuntu_18.04-cpython_3.6 .
	docker run ubuntu_18.04-cpython_3.6 2> tests-docker/ubuntu_18.04-CPython_3.6.txt

	tail tests-docker/ubuntu_18.04-CPython_3.6.txt
	
