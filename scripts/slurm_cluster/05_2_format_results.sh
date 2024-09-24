#!/bin/bash

# Get arguments
while getopts i:r:o:s:t: flag
do
    case "${flag}" in
        i) RESULT_DIR=${OPTARG};;
        r) FORM_RESULT_DIR=${OPTARG};;
        o) OBJECTIVES_DIR=${OPTARG};;
        s) SBML_DIR=${OPTARG};;
        t) TOOL=${OPTARG};;
        *) echo "Invalid OPTION" && exit 1;;
    esac
done

#SLURM_ARRAY_TASK_ID="1"
SPECIES=$(ls "$RESULT_DIR" | head -n "$SLURM_ARRAY_TASK_ID" | tail -n 1)
OBJECTIVE=$(head -n 1 $OBJECTIVES_DIR/${SPECIES}_target.txt)

$PYTHON_FILE="../05_format_results.py"

if [[ "$TOOL" = "NETSEED" ]]
then
    RESULT_FILE="$RESULT_DIR/$SPECIES/results.json"
    FORM_RESULT_FILE="$FORM_RESULT_DIR/${SPECIES}_netseed_results.json"
    python $PYTHON_FILE $RESULT_FILE $SPECIES $OBJECTIVE $FORM_RESULT_FILE $TOOL
    seed2lp flux "$SBML_DIR/${SPECIES}.xml" $FORM_RESULT_FILE $FORM_RESULT_DIR
else
    RESULTS_FILE_FN="$RESULT_DIR/$SPECIES/full_network/results.json"
    RESULTS_FILE_TGT="$RESULT_DIR/$SPECIES/biomass_target/results.json"
    FORM_RESULT_FILE_FN="$FORM_RESULT_DIR/${SPECIES}_precursor_fn_results.json"
    FORM_RESULT_FILE_TGT="$FORM_RESULT_DIR/${SPECIES}_precursor_tgt_results.json"
    python $PYTHON_FILE $RESULTS_FILE_FN $SPECIES $OBJECTIVE $FORM_RESULT_FILE_FN $TOOL
    python $PYTHON_FILE $RESULTS_FILE_TGT $SPECIES $OBJECTIVE $FORM_RESULT_FILE_TGT $TOOL

    seed2lp flux "$SBML_DIR/${SPECIES}.xml" $FORM_RESULT_FILE_FN $FORM_RESULT_DIR
    seed2lp flux "$SBML_DIR/${SPECIES}.xml" $FORM_RESULT_FILE_TGT $FORM_RESULT_DIR
fi






