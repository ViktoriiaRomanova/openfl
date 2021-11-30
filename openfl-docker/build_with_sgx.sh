#!/bin/bash
set -m

FEDERATION ?= fed_kvasir
# FEDERATION ?= fed_work12345alpha81671

docker build -t openfl_base:pre_sgx -f Dockerfile.base ..

docker build -t openfl_gramine -f Dockerfile.gramine ..

# Federation should not use CUDA-related packages
docker build -t ${FEDERATION} -f Dockerfile.workspace \
    --build-arg BASE_IMAGE=openfl_gramine \
    --build-arg WORKSPACE_NAME=${FEDERATION} \
    ${FEDERATION} 

# aggregator
# make sure user can write to monted folders on host machine "chmod -R a+rw fed_workspace"
# "cd aggregator_manifest"
# INSECURE: key is generated to the manifest dir with "openssl genrsa -3 -out key.pem 3072"
# Process is run from the manifest dir with "make clean && make SGX=1 SGX_SIGNER_KEY=key.pem"
FEDERATION=fed_work12345alpha81671
docker run -it --rm --network=host --device=/dev/sgx_enclave --device=/dev/sgx_provision \
    --volume=/var/run/aesmd:/var/run/aesmd \
    --volume=/home/idavidyu/openfl/openfl-docker/${FEDERATION}/cert:/home/user/workspace/cert \
    --volume=/home/idavidyu/openfl/openfl-docker/${FEDERATION}/plan:/home/user/workspace/plan \
    --volume=/home/idavidyu/openfl/openfl-docker/${FEDERATION}/logs:/home/user/workspace/logs \
    --mount type=bind,src=/home/idavidyu/openfl/openfl-docker/${FEDERATION}/save,dst=/home/user/workspace/save,readonly=0 \
    --mount type=bind,src=/home/idavidyu/openfl/openfl-docker/aggregator_manifest,dst=/home/user/workspace/aggregator_manifest,readonly=0 \
    ${FEDERATION} bash
    # --env no_proxy=${no_proxy},$(hostname --all-fqdns | awk '{print $1}') \
    # to run aggregator in container without gramine fx aggregator start

# collaborator
# Process is run from the manifest dir with "make clean && make SGX=1 SGX_SIGNER_KEY=key.pem"
COL_NAME=one123dragons
COL_NAME=beta34unicorns
FEDERATION=fed_work12345alpha81671
docker run -it --rm --network=host --device=/dev/sgx_enclave --device=/dev/sgx_provision \
    --volume=/var/run/aesmd:/var/run/aesmd \
    --volume=/home/idavidyu/.openfl/data:/home/user/workspace/data \
    --volume=/home/idavidyu/openfl/openfl-docker/${FEDERATION}/${COL_NAME}/${FEDERATION}/cert:/home/user/workspace/cert \
    --volume=/home/idavidyu/openfl/openfl-docker/${FEDERATION}/${COL_NAME}/${FEDERATION}/plan:/home/user/workspace/plan \
    --mount type=bind,src=/home/idavidyu/openfl/openfl-docker/collaborator_manifest,dst=/home/user/workspace/collaborator_manifest,readonly=0 \
    --env no_proxy=${no_proxy},$(hostname --all-fqdns | awk '{print $1}') \
    --env COL_NAME=${COL_NAME} \
    ${FEDERATION} bash
    
# make clean && rm collaborator.manifest.template && cp collaborator_manifest/collaborator.manifest.template . && make SGX=1 SGX_SIGNER_KEY=collaborator_manifest/key.pem
# pip uninstall -y torch && pip install torch==1.10.0+cpu torchvision==0.11.1+cpu torchaudio==0.10.0+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html


# docker run -it --rm --network=host --device=/dev/sgx_enclave --device=/dev/sgx_provision \
#     --volume=/var/run/aesmd:/var/run/aesmd \
#     --volume=/home/idavidyu/openfl/openfl-docker/sample_app:/sample_app \
#     openfl_gramine bash
