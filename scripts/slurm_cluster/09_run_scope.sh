#!/bin/bash

# Get arguments
while getopts i:s:n:b: flag
do
    case "${flag}" in
        i) SOLUTION_DIR=${OPTARG};;
        s) SCOPE_DIR=${OPTARG};;
        n) NORM_SBML_DIR=${OPTARG};;
        b)
          if [[ ! -z ${OPTARG} ]]; then
              SPECIES=${OPTARG}
          fi
        ;;
        *) echo "Invalid OPTION" && exit 1;;
    esac
done

# SERVER


if [[ ! -z ${SPECIES} ]]; then
  CURRENT_SPECIES=$SPECIES
  CURRENT_SBML_FILE="$NORM_SBML_DIR/${SPECIES}.xml"
else
  CURRENT_SBML_FILE=$(ls "$NORM_SBML_DIR" | head -n "$SLURM_ARRAY_TASK_ID" | tail -n 1)
  CURRENT_SPECIES=$(basename "$CURRENT_SBML_FILE" | sed 's/\.[^.]*$//')
fi


SPECIES_SOLUTION_DIR="$SOLUTION_DIR/$CURRENT_SPECIES/"

FULL_PATH=$SCOPE_DIR/$CURRENT_SPECIES
if [[ ! -d "$FULL_PATH" ]]
then
  mkdir -p "$FULL_PATH"
fi

for solution_file in "$SPECIES_SOLUTION_DIR"/*results.json
do
  seed2lp scope "$NORM_SBML_DIR/$CURRENT_SBML_FILE" $solution_file $FULL_PATH
done