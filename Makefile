mypy-check:
	mypy -m codecarbon \
	--ignore-missing-imports \
	--no-strict-optional \
	--disable-error-code attr-defined \
	--disable-error-code assignment \
	--disable-error-code misc \

pre-commit:
	# Use same syntax as GitHub pre-commit
	pre-commit run --show-diff-on-failure --color=always --all-files
