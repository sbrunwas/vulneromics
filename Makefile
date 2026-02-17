.PHONY: install run

install:
	bash scripts/install_deps.sh

run:
	streamlit run app.py
