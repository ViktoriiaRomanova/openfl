ARCH_LIBDIR ?= /lib/$(shell $(CC) -dumpmachine)
# ARCH_LIBDIR ?= /lib/x86_64-linux-gnu

# This is a signer key on a BUILDING machine
# In this case we have a key inside the container
SGX_SIGNER_KEY ?= /var/gramine/Pal/src/host/Linux-SGX/signer/enclave-key.pem
PYTHON ?= $(shell sh -c "command -v python3.8")
DATA_FOLDER ?= /home/user/workspace/data

ifeq ($(DEBUG),1)
GRAMINE_LOG_LEVEL = debug
else
GRAMINE_LOG_LEVEL = error
endif

.PHONY: all
all: collaborator.manifest
ifeq ($(SGX),1)
all: collaborator.manifest.sgx collaborator.sig collaborator.token
endif

# gramine-manifest -Dlog_level=debug -Darch_libdir=/lib/x86_64-linux-gnu -Dentrypoint=/usr/bin/python3.8 aggregator.manifest.template >aggregator.manifest
# python3.8 /usr/local/bin/gramine-manifest -Dlog_level=debug -Darch_libdir=/lib/x86_64-linux-gnu -Dentrypoint=/usr/bin/python3.8 aggregator.manifest.template >aggregator.manifest
collaborator.manifest: collaborator.manifest.template
	$(PYTHON) $(shell sh -c "command -v gramine-manifest") \
		-Dlog_level=$(GRAMINE_LOG_LEVEL) \
		-Darch_libdir=$(ARCH_LIBDIR) \
		-Dno_proxy=$(no_proxy) \
		-Dhttp_proxy=$(http_proxy) \
		-Dhttps_proxy=$(https_proxy) \
		-Ddata_folder=$(DATA_FOLDER) \
		-Dentrypoint=$(shell sh -c "command -v $(PYTHON)") \
		$< >$@

# gramine-sgx-sign --key /gramine/Pal/src/host/Linux-SGX/signer/enclave-key.pem --manifest collaborator.manifest --output collaborator.manifest.sgx
collaborator.manifest.sgx: collaborator.manifest
	@test -s $(SGX_SIGNER_KEY) || \
	    { echo "SGX signer private key was not found, please specify SGX_SIGNER_KEY!"; exit 1; }
	gramine-sgx-sign \
		--key $(SGX_SIGNER_KEY) \
		--manifest $< \
		--output $@

collaborator.sig: collaborator.manifest.sgx

# gramine-sgx-get-token --output collaborator.token --sig collaborator.sig
collaborator.token: collaborator.sig
	gramine-sgx-get-token --output $@ --sig $<

# gramine-sgx ./collaborator main.py bar
.PHONY: run
run: all
# gramine-sgx ./collaborator -c "$(cat < $(which fx))" collaborator start -n ${COL_NAME}

.PHONY: clean
clean:
	$(RM) *.manifest *.manifest.sgx *.token *.sig OUTPUT* *.PID TEST_STDOUT TEST_STDERR
	$(RM) -r scripts/__pycache__

.PHONY: distclean
distclean: clean