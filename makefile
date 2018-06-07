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
