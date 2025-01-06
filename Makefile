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

ZP = $(TOP)/zynq-parrot
ZP_EX = black-parrot-example
ZP_SIM = $(ZP)/cosim/$(ZP_EX)/verilator

CASCADE_DIR = $(TOP)/cascade-meta
CASCADE_ENV = $(CASCADE_DIR)/env.sh
CASCADE_PY = $(CASCADE_DIR)/fuzzer/do_genmanyelfs.py
export CASCADE_BP = $(ZP)/cosim/import/black-parrot
export CASCADE_BP_SDK_DIR = $(ZP)/cosim/import/black-parrot-sdk

FIRST = 0
LAST = 10
CGS = $(shell seq -s " " $(FIRST) $(LAST))

RUN_DIR = $(TOP)/runs
TEST = test

%.cascade:
	mkdir -p $(RUN_DIR)/$*
	source $(CASCADE_ENV) && \
	$(PYTHON) $(CASCADE_PY) "$(PROBS)" 1 $(RUN_DIR)/$* $(TEST)
	$(RV_OBJDUMP) $(RUN_DIR)/$*/$(TEST).riscv > $(RUN_DIR)/$*/$(TEST).dump

%.run:
	make -C $(ZP_SIM) run NBF_FILE=$(abspath $(RUN_DIR)/$*/$(TEST).nbf) COV_EN=1 RAND_COV=0 COV_NUM=$(words $(CGS))
	for cg in $(CGS); do \
		sort -u $(addprefix $(ZP_SIM)/,$(addsuffix .raw,$$cg)) > $(RUN_DIR)/$*/$(addsuffix .raw,$$cg); \
		sort -u $(addprefix $(ZP_SIM)/,$(addsuffix .align,$$cg)) > $(RUN_DIR)/$*/$(addsuffix .align,$$cg); \
	done

%.reward: | $(BEST)
	@touch $(RUN_DIR)/$*/diff
	@for cg in $(CGS); do \
		comm -1 -3 $(RUN_DIR)/$(BEST)/$(addsuffix .$(COV_T),$$cg) $(RUN_DIR)/$*/$(addsuffix .$(COV_T),$$cg) >> $(RUN_DIR)/$*/diff; \
	done
	@wc -l $(RUN_DIR)/$*/diff | awk '{print $$1;}'
	@rm -rf $(RUN_DIR)/$*/diff

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

clean:
	$(MAKE) -C $(ZP_SIM) clean

bleach: clean
	rm -rf $(RUN_DIR)
	rm -rf __pycache__
