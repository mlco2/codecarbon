mypy-check:
	mypy -m codecarbon \
	--ignore-missing-imports \
	--no-strict-optional \
	--disable-error-code attr-defined \
	--disable-error-code assignment \
	--disable-error-code misc \
