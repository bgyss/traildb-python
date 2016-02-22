.PHONY: test

all:
	python setup.py build
	python setup.py build_ext
	sudo python setup.py install

test:
	python test/test.py
	python test/test_filters.py
