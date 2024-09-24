#!/bin/bash

# Get arguments
while getopts i:r: flag
do
    case "${flag}" in
        i) IN_DIRECTORY=${OPTARG};;
        r) RESULT_DIR=${OPTARG};;
        *) echo "Invalid OPTION" && exit 1;;
    esac
done

#SLURM_ARRAY_TASK_ID=1
CURRENT_FILE=$(ls "$IN_DIRECTORY" | head -n "$SLURM_ARRAY_TASK_ID" | tail -n 1)


CURRENT_SPECIES=$(basename "$CURRENT_FILE" | sed 's/\.[^.]*$//')


# Create directories if needed
if [[ ! -d "$RESULT_DIR" ]]
then
  mkdir -p "$RESULT_DIR"
fi


seed2lp network "$IN_DIRECTORY/$CURRENT_FILE" "$RESULT_DIR" -wf
