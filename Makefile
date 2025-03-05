SHELL := /bin/bash

TOP = $(CURDIR)

ALIGN ?= 0
ifeq ($(ALIGN),0)
COV_T = raw
else
COV_T = align
endif

PYTHON = python3.9
RV_OBJDUMP = riscv64-unknown-elf-objdump -d
RV_OBJCOPY = riscv64-unknown-elf-objcopy -O verilog

ZP = $(TOP)/zynq-parrot
ZP_EX = black-parrot-example
ZP_SIM = $(ZP)/cosim/$(ZP_EX)/verilator
ZP_NBF = $(ZP)/cosim/import/black-parrot/bp_common/software/py/nbf.py

CASCADE_DIR = $(TOP)/cascade-meta
CASCADE_ENV = $(CASCADE_DIR)/env.sh
CASCADE_PY = $(CASCADE_DIR)/fuzzer/do_genmanyelfs.py
export CASCADE_BP = $(ZP)/cosim/import/black-parrot
export CASCADE_BP_SDK_DIR = $(ZP)/software/import/black-parrot-sdk

FIRST = 0
LAST = 9
CGS = $(shell seq -s " " $(FIRST) $(LAST))

RUN_DIR = $(TOP)/runs.$(COV_T)
TEST = test

TIMEOUT = 3m

libs:
	git submodule update --init cascade-meta
	git submodule update --init zynq-parrot
	cd zynq-parrot && \
		git submodule update --init --recursive cosim/import/black-parrot && \
		git submodule update --init --recursive cosim/import/basejump_stl && \
		git submodule update --init --recursive cosim/import/black-parrot-subsystems && \
		git submodule update --init --recursive cosim/import/black-parrot-tools && \
		cd cosim/black-parrot-example && ./instrument.sh

%.cascade:
	mkdir -p $(RUN_DIR)/$*
	source $(CASCADE_ENV) && \
	$(PYTHON) $(CASCADE_PY) "$(PROBS)" 1 $(RUN_DIR)/$* $(TEST)
	$(RV_OBJDUMP) $(RUN_DIR)/$*/$(TEST).elf > $(RUN_DIR)/$*/$(TEST).dump
	$(RV_OBJCOPY) $(RUN_DIR)/$*/$(TEST).elf $(RUN_DIR)/$*/$(TEST).mem
	sed -i "s/@8/@0/g" $(RUN_DIR)/$*/$(TEST).mem
	$(PYTHON) $(ZP_NBF) --debug --skip_zeros --config --ncpus 1 --boot_pc 0x80000000 --mem $(RUN_DIR)/$*/$(TEST).mem > $(RUN_DIR)/$*/$(TEST).nbf

%.run:
	make -C $(ZP_SIM) build COV_EN=1 RAND_COV=0 COV_NUM=$(words $(CGS))
	timeout $(TIMEOUT) make -C $(ZP_SIM) run NBF_FILE=$(abspath $(RUN_DIR)/$*/$(TEST).nbf) COV_EN=1 RAND_COV=0 COV_NUM=$(words $(CGS)) || echo "timeout"
	for cg in $(CGS); do \
		sort -u $(addprefix $(ZP_SIM)/,$(addsuffix .raw,$$cg)) > $(RUN_DIR)/$*/$(addsuffix .raw,$$cg); \
		sort -u $(addprefix $(ZP_SIM)/,$(addsuffix .align,$$cg)) > $(RUN_DIR)/$*/$(addsuffix .align,$$cg); \
	done

%.reward: | $(BEST)
	touch $(RUN_DIR)/$*/$(BEST).diff
	for cg in $(CGS); do \
		comm -1 -3 $(RUN_DIR)/$(BEST)/$(addsuffix .$(COV_T),$$cg) $(RUN_DIR)/$*/$(addsuffix .$(COV_T),$$cg) >> $(RUN_DIR)/$*/$(BEST).diff; \
	done
	wc -l $(RUN_DIR)/$*/$(BEST).diff | awk '{print $$1;}'
	#rm -rf $(RUN_DIR)/$*/$(BEST).diff

%.update: | $(BEST)
	for cg in $(CGS); do \
		cat $(RUN_DIR)/$*/$(addsuffix .raw,$$cg) >> $(RUN_DIR)/$(BEST)/$(addsuffix .raw,$$cg); \
		cat $(RUN_DIR)/$*/$(addsuffix .align,$$cg) >> $(RUN_DIR)/$(BEST)/$(addsuffix .align,$$cg); \
		sort -u -o $(RUN_DIR)/$(BEST)/$(addsuffix .raw,$$cg) $(RUN_DIR)/$(BEST)/$(addsuffix .raw,$$cg); \
		sort -u -o $(RUN_DIR)/$(BEST)/$(addsuffix .align,$$cg) $(RUN_DIR)/$(BEST)/$(addsuffix .align,$$cg); \
	done

$(BEST):
	mkdir -p $(RUN_DIR)/$(BEST)
	for cg in $(CGS); do \
		touch $(RUN_DIR)/$(BEST)/$(addsuffix .raw,$$cg); \
		touch $(RUN_DIR)/$(BEST)/$(addsuffix .align,$$cg); \
	done

%.craw:
	touch $(RUN_DIR)/$*/all
	for cg in $(CGS); do \
		cat $(RUN_DIR)/$*/$(addsuffix .raw,$$cg) >> $(RUN_DIR)/$*/all; \
	done
	wc -l $(RUN_DIR)/$*/all | awk '{print $$1;}'
	rm -rf $(RUN_DIR)/$*/all

%.calign:
	touch $(RUN_DIR)/$*/all
	for cg in $(CGS); do \
		cat $(RUN_DIR)/$*/$(addsuffix .align,$$cg) >> $(RUN_DIR)/$*/all; \
	done
	wc -l $(RUN_DIR)/$*/all | awk '{print $$1;}'
	rm -rf $(RUN_DIR)/$*/all

%.rm:
	rm -rf $(RUN_DIR)/$*

clean:
	$(MAKE) -C $(ZP_SIM) clean
	rm -rf $(ZP_SIM)/*.raw
	rm -rf $(ZP_SIM)/*.align
	rm -rf __pycache__

bleach:
	@echo -n "Are you sure you want to clear all data? [y/N] " && read ans && [ $${ans:-N} = y ]
	$(MAKE) clean
	rm -rf runs.*

########################################
MAB_ITER ?= 10000
MAB_ARMS ?= 10
MAB_GAMMA ?= 0.1
MAB_KNOBS ?= 14
MAB_ALPHA ?= 0.25
MAB_SATW ?= 3

mab:
	$(PYTHON) -u mab.py \
	--iterations $(MAB_ITER) --arms $(MAB_ARMS) --gamma $(MAB_GAMMA) \
	--knobs $(MAB_KNOBS) --alpha $(MAB_ALPHA) --satw $(MAB_SATW) \
	|& tee mab.$(COV_T).log

