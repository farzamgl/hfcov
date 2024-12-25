TOP = $(CURDIR)

ALIGN ?= 1
ALGO ?= mab
ALGO_PY = $(TOP)/$(ALGO)/$(ALGO).py

PYTHON = python3.9

ZP = $(TOP)/zynq-parrot
ZP_EX = black-parrot-example
ZP_SIM = $(ZP)/cosim/$(ZP_EX)/verilator

CASCADE_DIR = $(TOP)/cascade-meta
CASCADE_ENV = $(CASCADE_DIR)/env.sh
CASCADE_PY = $(CASCADE_DIR)/fuzzer/do_fuzzsingle.py

FIRST = 0
LAST = 10
CGS = $(shell seq -s " " $(FIRST) $(LAST))

RUN_DIR = $(TOP)/run

#TODO: fix this
%.cascade:
	. $(CASCADE_ENV)
	$(PYTHON) $(CASCADE_PY) $(PROBS)

%.run: $(NBF_FILE)
	mkdir -p $(RUN_DIR)/$*
	make -C $(ZP_SIM) run NBF_FILE=$(abspath $<) COV_EN=1 RAND_COV=0 COV_NUM=$(words $(CGS))
	for cg in $(CGS); do \
		sort -u $(addprefix $(ZP_SIM)/,$(addsuffix .raw,$$cg)) > $(RUN_DIR)/$*/$(addsuffix .raw,$$cg); \
		sort -u $(addprefix $(ZP_SIM)/,$(addsuffix .align,$$cg)) > $(RUN_DIR)/$*/$(addsuffix .align,$$cg); \
	done

%.reward:
	@mkdir -p $(RUN_DIR)/best
	@touch $(RUN_DIR)/$*/diff
ifeq ($(ALIGN),0)
	@for cg in $(CGS); do \
		touch $(RUN_DIR)/best/$(addsuffix .raw,$$cg); \
		comm -1 -3 $(RUN_DIR)/best/$(addsuffix .raw,$$cg) $(RUN_DIR)/$*/$(addsuffix .raw,$$cg) >> $(RUN_DIR)/$*/diff; \
	done
else
	@for cg in $(CGS); do \
		touch $(RUN_DIR)/best/$(addsuffix .align,$$cg); \
		comm -1 -3 $(RUN_DIR)/best/$(addsuffix .align,$$cg) $(RUN_DIR)/$*/$(addsuffix .align,$$cg) >> $(RUN_DIR)/$*/diff; \
	done
endif
	@wc -l $(RUN_DIR)/$*/diff | awk '{print $$1;}'
	@rm -rf $(RUN_DIR)/$*/diff

%.update:
	for cg in $(CGS); do \
		cat $(RUN_DIR)/$*/$(addsuffix .raw,$$cg) >> $(RUN_DIR)/best/$(addsuffix .raw,$$cg); \
		cat $(RUN_DIR)/$*/$(addsuffix .align,$$cg) >> $(RUN_DIR)/best/$(addsuffix .align,$$cg); \
		sort -u -o $(RUN_DIR)/best/$(addsuffix .raw,$$cg) $(RUN_DIR)/best/$(addsuffix .raw,$$cg); \
		sort -u -o $(RUN_DIR)/best/$(addsuffix .align,$$cg) $(RUN_DIR)/best/$(addsuffix .align,$$cg); \
	done

clean:
	$(MAKE) -C $(ZP_SIM) clean

bleach: clean
	rm -rf $(RUN_DIR)
	rm -rf __pycache__
