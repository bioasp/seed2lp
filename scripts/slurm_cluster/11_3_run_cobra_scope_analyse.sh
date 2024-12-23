#!/bin/bash

# Get arguments
while getopts r:s:o: flag
do
    case "${flag}" in
        r) SCOPE_DIR=${OPTARG};;
        s) SBML_DIR=${OPTARG};;
        o) OBJECTIVE_DIR=${OPTARG};;
        *) echo "Invalid OPTION" && exit 1;;
    esac
done


#SLURM_ARRAY_TASK_ID=1
CURRENT_FILE=$(ls "$SBML_DIR" | head -n "$SLURM_ARRAY_TASK_ID" | tail -n 1)
CURRENT_SPECIES=$(basename "$CURRENT_FILE" | sed 's/\.[^.]*$//')


FULL_PATH_SCOPE=$SCOPE_DIR/$CURRENT_SPECIES/scope
FULL_PATH_SEEDS=$SCOPE_DIR/$CURRENT_SPECIES/sbml


modes_info=cobrapy/cobrapy/other/no_accu
CURRENT_PATH_SEED=$FULL_PATH_SEEDS/$modes_info/
CURRENT_PATH_SCOPE=$FULL_PATH_SCOPE/$modes_info/
python ../10_1_scope_analyse.py ${CURRENT_SPECIES} "${SBML_DIR}/${CURRENT_FILE}" ${CURRENT_PATH_SCOPE} ${CURRENT_PATH_SEED} "${OBJECTIVE_DIR}/${CURRENT_SPECIES}_target.txt" cobrapy
