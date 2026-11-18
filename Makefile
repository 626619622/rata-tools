PYTHON ?= python

.PHONY: lock test wheel container verify

lock:
	$(PYTHON) scripts/lock_dependencies.py

test:
	$(PYTHON) -m unittest discover -s tests -v

wheel:
	$(PYTHON) -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .

container:
	docker build -t rata-tools:0.2.1 .

verify: test wheel
