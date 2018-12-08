#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$DIR/common.sh"
read_reactor_rc
detect_ci

# Agave API integration
AGAVE_CREDS="${AGAVE_CACHE_DIR}"
log "Pulling API credentials from ${AGAVE_CREDS}"
if [ ! -d "${AGAVE_CREDS}" ]; then
    AGAVE_CREDS="${HOME}/.agave"
    # Refresh them with a call to Agave.restore()
    if ((AGAVE_PREFER_PYTHON)); then
        log "Refreshing using AgavePy"
        eval python ${DIR}/refresh_agave_credentials.py
    else
        log "Refreshing using CLI"
        auth-tokens-refresh -S
    fi
fi
if [ ! -f "${AGAVE_CREDS}/current" ]; then
    die "No Agave API credentials found in ${AGAVE_CREDS}"
fi

TOKEN=$(jq -r  .access_token ~/.agave/current)

# Load up the message to send
if [ ! -z "$1" ]; then
    MESSAGE_PATH=$1
else
    MESSAGE_PATH="tests/data/local-message-01.json"
fi
MESSAGE=
if [ -f "${MESSAGE_PATH}" ]; then
    MESSAGE=$(jq -rc . ${MESSAGE_PATH})
fi
if [ -z "${MESSAGE}" ]; then
    die "Message not readable from ${MESSAGE_PATH}"
fi

if [ -z "$ACTOR_ID" ];
then
    if [ -f .ACTOR_ID ];
    then
        ACTOR_ID=$(cat .ACTOR_ID)
    else
        die "No .ACTOR_ID file found"
    fi
fi

CMD="abaco run -v -z ${TOKEN} -m '${MESSAGE}' ${ACTOR_ID}"

echo ${CMD}

CMD="${CMD} | jq -C ."

eval ${CMD}
