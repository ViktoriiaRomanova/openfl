ARCH_LIBDIR ?= /lib/$(shell $(CC) -dumpmachine)
# ARCH_LIBDIR ?= /lib/x86_64-linux-gnu

# This is a signer key on a BUILDING machine
# In this case we have a key inside the container
SGX_SIGNER_KEY ?= /var/gramine/Pal/src/host/Linux-SGX/signer/enclave-key.pem
PYTHON ?= $(shell sh -c "command -v python3.8")

ifeq ($(DEBUG),1)
GRAMINE_LOG_LEVEL = debug
else
GRAMINE_LOG_LEVEL = error
endif

.PHONY: all
all: aggregator.manifest
ifeq ($(SGX),1)
all: aggregator.manifest.sgx aggregator.sig aggregator.token
endif

# gramine-manifest -Dlog_level=debug -Darch_libdir=/lib/x86_64-linux-gnu -Dentrypoint=/usr/bin/python3.8 aggregator.manifest.template >aggregator.manifest
# python3.8 /usr/local/bin/gramine-manifest -Dlog_level=debug -Darch_libdir=/lib/x86_64-linux-gnu -Dentrypoint=/usr/bin/python3.8 aggregator.manifest.template >aggregator.manifest
aggregator.manifest: aggregator.manifest.template
	$(PYTHON) $(shell sh -c "command -v gramine-manifest") \
		-Dlog_level=$(GRAMINE_LOG_LEVEL) \
		-Darch_libdir=$(ARCH_LIBDIR) \
		-Dentrypoint=$(shell sh -c "command -v $(PYTHON)") \
		$< >$@
# -Dno_proxy=$(no_proxy) \
# -Dhttp_proxy=$(http_proxy) \
# -Dhttps_proxy=$(https_proxy) \

# gramine-sgx-sign --key /gramine/Pal/src/host/Linux-SGX/signer/enclave-key.pem --manifest aggregator.manifest --output aggregator.manifest.sgx
aggregator.manifest.sgx: aggregator.manifest
	@test -s $(SGX_SIGNER_KEY) || \
	    { echo "SGX signer private key was not found, please specify SGX_SIGNER_KEY!"; exit 1; }
	gramine-sgx-sign \
		--key $(SGX_SIGNER_KEY) \
		--manifest $< \
		--output $@

aggregator.sig: aggregator.manifest.sgx

# gramine-sgx-get-token --output aggregator.token --sig aggregator.sig
aggregator.token: aggregator.sig
	gramine-sgx-get-token --output $@ --sig $<

# gramine-sgx ./aggregator main.py bar
.PHONY: run
run: all
# gramine-sgx ./aggregator -c "$(cat < $(which fx))" aggregator start

.PHONY: clean
clean:
	$(RM) *.manifest *.manifest.sgx *.token *.sig OUTPUT* *.PID TEST_STDOUT TEST_STDERR
	$(RM) -r scripts/__pycache__

.PHONY: distclean
distclean: clean