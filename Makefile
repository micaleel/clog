PORT=5000
all:
	@echo "Doing everything"

install:
	@echo "📦 Installing Clog ... "
	@./install.sh

uninstall:
	rm -rvf .venv

black:
	black .

test:
	pytest -v ./tests
