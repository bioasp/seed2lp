#!/bin/bash

# Get arguments
while getopts s:o:r: flag
do
    case "${flag}" in
        s) SBML_DIR=${OPTARG};;
        o) OBJECTIVE_DIR=${OPTARG};;
        r) RESULT_DIR=${OPTARG};;
        *) echo "Invalid OPTION" && exit 1;;
    esac
done


#SLURM_ARRAY_TASK_ID=1
CURRENT_SBML_FILE=$(ls "$SBML_DIR" | head -n "$SLURM_ARRAY_TASK_ID" | tail -n 1)
CURRENT_SPECIES=$(basename "$CURRENT_SBML_FILE" | sed 's/\.[^.]*$//')
SBML_FILE=$SBML_DIR/$CURRENT_SBML_FILE
PATH_OBJECTIVE=$OBJECTIVE_DIR/${CURRENT_SPECIES}_target.txt

python ../12_1_phylomint_seedsearch.py $SBML_FILE $PATH_OBJECTIVE $RESULT_DIR