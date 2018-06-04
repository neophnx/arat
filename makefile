tests2: clean
	python2 -m nose --processes=-1 -v --with-coverage --with-doctest tests standalone.py server/src

tests3: clean
	python3 -m nose --processes=-1 -v --with-coverage --with-doctest tests standalone.py server/src


clean:
	find . -name "*.pyc" |xargs rm
