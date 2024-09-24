#!/bin/bash

# Get arguments
while getopts d:o:i:n:r:t: flag
do
    case "${flag}" in
        d) 
          if [[ ! -z ${OPTARG} ]]; then
              TARGET_DIR="${OPTARG}/target"
          fi
        ;;
        o) 
          if [[ ! -z ${OPTARG} ]]; then
              read -r OBJECTIVE < ${OPTARG}
          fi
        ;;
        i) SBML_DIR=${OPTARG};;
        n) N2PCOMP_DIR=${OPTARG};;
        r) RESULT_DIR=${OPTARG};;
        t) TOOL=${OPTARG};;
    esac
done



if [[ "$TOOL" = "NETSEED" ]]
then
  CONF_PATH="${N2PCOMP_DIR}/config_netseed.yaml"
else
  CONF_PATH="${N2PCOMP_DIR}/config_precursor.yaml"
  # Create directories if needed
  if [[ ! -d "$TARGET_DIR" ]]
  then
    mkdir -p "$TARGET_DIR"
  fi
fi

# Create directories if needed
if [[ ! -d "$RESULT_DIR" ]]
then
  mkdir -p "$RESULT_DIR"
fi

for file in $(find  "$SBML_DIR"/ -maxdepth 1 -mindepth 1 -type f -print);
do
  CURRENT_SPECIES=$(basename $file | sed 's/\.[^.]*$//')

  if [[ ! -d "$RESULT_DIR/$CURRENT_SPECIES" ]]
  then
    mkdir -p "$RESULT_DIR/$CURRENT_SPECIES"
  fi

  if [[ "$TOOL" = "NETSEED" ]]
  then
    python -m n2pcomp run "$file" \
      --output "${RESULT_DIR}/$CURRENT_SPECIES/" \
      -c $CONF_PATH -nbs 1000 -tl 45
  else
    if [[ ! -d "$RESULT_DIR/$CURRENT_SPECIES/full_network" ]]
    then
      mkdir -p "$RESULT_DIR/$CURRENT_SPECIES/full_network"
    fi

    if [[ ! -d "$RESULT_DIR/$CURRENT_SPECIES/target" ]]
    then
      mkdir -p "$RESULT_DIR/$CURRENT_SPECIES/target"
    fi

    #Split Array
    python seed2lp $file $TARGET_DIR -o $OBJECTIVE


    python -m n2pcomp run $file \
    --output "${RESULT_DIR}/$CURRENT_SPECIES/target" \
    -c $CONF_FILE -nbs 1000 -tl 45 \
    -t "$TARGET_DIR/${CURRENT_SPECIES}_targets.txt"

    python -m n2pcomp run $file \
    --output "${RESULT_DIR}/$CURRENT_SPECIES/full_network" \
    -c $CONF_FILE -nbs 1000 -tl 45
  fi

done