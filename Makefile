TOP = $(CURDIR)

ALIGN ?= 1
ALGO ?= mab
ALGO_PY = $(TOP)/$(ALGO)/$(ALGO).py

PYTHON = python3.9

ZP = $(TOP)/zynq-parrot
ZP_EX = black-parrot-example
ZP_SIM = $(ZP)/cosim/$(ZP_EX)/verilator

FIRST = 0
LAST = 10
CGS = $(shell seq -s " " $(FIRST) $(LAST))

init:
	mkdir -p best
	for cg in $(CGS); do \
		touch best/$(addsuffix .raw,$$cg); \
		touch best/$(addsuffix .align,$$cg); \
	done

%.run: $(NBF_FILE)
	make -C $(ZP_SIM) run NBF_FILE=$(abspath $<)

%.cov:
	mkdir -p run.$*
	for cg in $(CGS); do \
		sort -u $(addprefix $(ZP_SIM)/,$(addsuffix .raw,$$cg)) > run.$*/$(addsuffix .raw,$$cg); \
		sort -u $(addprefix $(ZP_SIM)/,$(addsuffix .align,$$cg)) > run.$*/$(addsuffix .align,$$cg); \
	done

%.reward:
	@touch run.$*/diff
ifeq ($(ALIGN),0)
	@for cg in $(CGS); do \
		comm -1 -3 best/$(addsuffix .raw,$$cg) run.$*/$(addsuffix .raw,$$cg) >> run.$*/diff; \
	done
else
	@for cg in $(CGS); do \
		comm -1 -3 best/$(addsuffix .align,$$cg) run.$*/$(addsuffix .align,$$cg) >> run.$*/diff; \
	done
endif
	@wc -l run.$*/diff | awk '{print $$1;}'
	@rm -rf run.$*/diff

%.update:
	for cg in $(CGS); do \
		cat run.$*/$(addsuffix .raw,$$cg) >> best/$(addsuffix .raw,$$cg); \
		cat run.$*/$(addsuffix .align,$$cg) >> best/$(addsuffix .align,$$cg); \
		sort -u -o best/$(addsuffix .raw,$$cg) best/$(addsuffix .raw,$$cg); \
		sort -u -o best/$(addsuffix .align,$$cg) best/$(addsuffix .align,$$cg); \
	done

fuzz: init
	$(PYTHON) $(ALGO_PY) 2>&1 | tee run.log

clean:
	$(MAKE) -C $(ZP_SIM) clean

bleach: clean
	rm -rf run.*
	rm -rf best
