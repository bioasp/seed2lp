#!/bin/bash

# Get arguments
while getopts s:o:t: flag
do
    case "${flag}" in
        s) SBML_DIR=${OPTARG};;
        o) OBJECTIVE_DIR=${OPTARG};;
        t) TARGET_DIR=${OPTARG};;
        *) echo "Invalid OPTION" && exit 1;;
    esac
done

#SLURM_ARRAY_TASK_ID=1
CURRENT_FILE=$(ls "$SBML_DIR" | head -n "$SLURM_ARRAY_TASK_ID" | tail -n 1)

CURRENT_SPECIES=$(basename "$CURRENT_FILE" | sed 's/\.[^.]*$//')
OBJECTIVE=$(head -n 1 $OBJECTIVES_DIR/${SPECIES}_target.txt)

# Create directories if needed
if [[ ! -d "$TARGET_DIR" ]]
then
  mkdir -p "$TARGET_DIR"
fi

seed2lp objective_targets $SBML_DIR/$CURRENT_FILE $TARGET_DIR -o $OBJECTIVE
