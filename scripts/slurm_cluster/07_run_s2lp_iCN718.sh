#!/bin/bash

# Get arguments
while getopts i:r:c:t:o:m:a:s: flag
do
    case "${flag}" in
        i) IN_DIRECTORY=${OPTARG};;
        r) RESULT_DIR=${OPTARG};;
        c) COMMAND=${OPTARG};;
        t) 
          if [[ ! -z ${OPTARG} ]]; then
              TEMP=${OPTARG}
          fi
        ;;
        o) OBJECTIVE_DIR=${OPTARG};;
        m) 
          if [[ ! -z ${OPTARG} ]]; then
              MAXIMIZATION=${OPTARG}
          fi
        ;;
        a) 
          if [[ ! -z ${OPTARG} ]]; then
              ACCUMULATION=${OPTARG}
          fi
        ;;
        s) 
          if [[ ! -z ${OPTARG} ]]; then
              SOLVE=${OPTARG}
          fi
        ;;
        *) echo "Invalid OPTION" && exit 1;;
    esac
done

CURRENT_SPECIES="iCN718"

CURRENT_FILE="${CURRENT_SPECIES}.xml"
OBJECTIVE_PATH="$OBJECTIVE_DIR/${CURRENT_SPECIES}_target.txt"

FULL_PATH=$RESULT_DIR
# Create directories if needed
if [[ ! -d "$FULL_PATH" ]]
then
  mkdir -p "$FULL_PATH"
fi

FULL_PATH=$FULL_PATH/$CURRENT_SPECIES
if [[ ! -d "$FULL_PATH" ]]
then
  mkdir -p "$FULL_PATH"
fi

OPTION=""
if [[ "$COMMAND" = "target" ]]
then
  OPTION="-tf $OBJECTIVE_PATH"
else
  read -r OBJECTIVE < $OBJECTIVE_PATH
  OPTION=" -o $OBJECTIVE"
fi

if [[ ! -z ${MAXIMIZATION} ]]; then
    OPTION="${OPTION} -max"
fi

if [[ ! -z ${ACCUMULATION} ]]; then
    OPTION="${OPTION} -accu"
fi

if [[ ! -z ${SOLVE} ]]; then
    OPTION="${OPTION} -so ${SOLVE}"
fi

seed2lp $COMMAND "$IN_DIRECTORY/$CURRENT_FILE" \
        "$FULL_PATH" \
        --temp $TEMP \
        -tl 0 -nbs 2000 -cf $OPTION \
        -m subsetmin