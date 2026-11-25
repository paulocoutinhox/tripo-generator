.DEFAULT_GOAL := help

UV ?= uv
RUN = PYTHONPATH=. $(UV) run --locked --env-file .env

.PHONY: help install test lint format balance character-cartoon character-realistic item-cartoon item-realistic item-image-cartoon character-image-cartoon

help:
	@echo "tripo-generator commands"
	@echo "  make install                  install the development tools with uv and create .env"
	@echo "  make test                     run the offline test suite"
	@echo "  make lint                     check the code"
	@echo "  make format                   format and fix the code"
	@echo "  make balance                  show the Tripo account balance"
	@echo "  make character-cartoon        generate the cartoon knight (paid)"
	@echo "  make character-realistic      generate the realistic knight (paid)"
	@echo "  make item-cartoon             generate the cartoon chest (paid)"
	@echo "  make item-realistic           generate the realistic chest (paid)"
	@echo "  make item-image-cartoon       generate the cartoon chest from its reference image (paid)"
	@echo "  make character-image-cartoon  generate the animated cartoon knight from its reference image (paid)"

install:
	$(UV) sync --locked --all-groups
	@test -f .env || cp .env.example .env

test:
	$(UV) run --locked python -m unittest discover -s tests -v

lint:
	$(UV) run --locked ruff check .
	$(UV) run --locked ruff format --check .

format:
	$(UV) run --locked ruff check --fix .
	$(UV) run --locked ruff format .

balance:
	$(RUN) python -c 'from tripo import get_balance; print(get_balance())'

character-cartoon:
	$(RUN) python examples/character-cartoon.py

character-realistic:
	$(RUN) python examples/character-realistic.py

item-cartoon:
	$(RUN) python examples/item-cartoon.py

item-realistic:
	$(RUN) python examples/item-realistic.py

item-image-cartoon:
	$(RUN) python examples/item-image-cartoon.py

character-image-cartoon:
	$(RUN) python examples/character-image-cartoon.py
