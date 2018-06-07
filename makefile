tests2: clean
	python2 -m nose --processes=-1 -v --with-coverage --with-doctest tests standalone.py server/src

tests3: clean
	python3 -m nose --processes=-1 -v --with-coverage --with-doctest tests standalone.py server/src

lint2:
	autopep8 -i $(DOC)
	python2 -m pylint $(DOC)

clean:
	find . -name "*.pyc" | xargs rm -f
	find data -name ".stats_cache" |xargs rm -f
