# THE ABOVE — build orchestration
# Pinned engine (see docs/decisions/0001-godot-version.md)
GODOT ?= $(HOME)/apps/godot-4.5.2/godot
PY ?= python3

.PHONY: art run test pytest tour tour-scene export-web export-linux export-windows resources

art:
	cd artgen && $(PY) -m artgen build

run:
	$(GODOT) --path game

test:
	$(GODOT) --path game --headless -s -d addons/gdUnit4/bin/GdUnitCmdTool.gd --ignoreHeadlessMode -a res://tests

pytest:
	cd artgen && $(PY) -m pytest tests -q

tour:
	$(GODOT) --path game -- --screenshot-tour --out=../artifacts/shots

tour-scene:
	$(GODOT) --path game -- --screenshot-scene $(SCENE) --out=../artifacts/shots

resources:
	$(GODOT) --path game --headless --script res://tools/gen_resources.gd

export-web:
	mkdir -p artifacts/export/web
	$(GODOT) --path game --headless --export-release "Web" ../artifacts/export/web/index.html

export-linux:
	mkdir -p artifacts/export/linux
	$(GODOT) --path game --headless --export-release "Linux" ../artifacts/export/linux/the_above.x86_64

export-windows:
	mkdir -p artifacts/export/windows
	$(GODOT) --path game --headless --export-release "Windows" ../artifacts/export/windows/the_above.exe
