dev:
	flit install -s --deps=develop --extras stats

format:
	black .
