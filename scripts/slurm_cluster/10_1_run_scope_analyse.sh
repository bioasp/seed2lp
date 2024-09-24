#!/bin/bash

# Get arguments
while getopts r:s:o:a:b:c:d:n: flag
do
    case "${flag}" in
        r) SCOPE_DIR=${OPTARG};;
        s) SBML_DIR=${OPTARG};;
        o) OBJECTIVE_DIR=${OPTARG};;
        a) LIST_DIR_LEV1=${OPTARG};;
        b) LIST_DIR_LEV2=${OPTARG};;
        c) LIST_DIR_LEV3=${OPTARG};;
        d) LIST_DIR_LEV4=${OPTARG};;
        n)
          if [[ ! -z ${OPTARG} ]]; then
              SPECIES=${OPTARG}
          fi
        ;;
        *) echo "Invalid OPTION" && exit 1;;
    esac
done


if [[ ! -z ${SPECIES} ]]; then
  CURRENT_SPECIES=$SPECIES
  CURRENT_SBML_FILE="$SBML_DIR/${SPECIES}.xml"
else
  CURRENT_FILE=$(ls "$SBML_DIR" | head -n "$SLURM_ARRAY_TASK_ID" | tail -n 1)
  CURRENT_SPECIES=$(basename "$CURRENT_FILE" | sed 's/\.[^.]*$//')
fi

FULL_PATH_SCOPE=$SCOPE_DIR/$CURRENT_SPECIES/scope
FULL_PATH_SEEDS=$SCOPE_DIR/$CURRENT_SPECIES/sbml



for dir_lev1 in ${LIST_DIR_LEV1[@]}; 
do
    for dir_lev2 in ${LIST_DIR_LEV2[@]}; 
    do
        for dir_lev3 in ${LIST_DIR_LEV3[@]}; 
        do
            for dir_lev4 in ${LIST_DIR_LEV4[@]}; 
            do
                modes_info=$dir_lev1/$dir_lev2/$dir_lev3/$dir_lev4
                CURRENT_PATH_SEED=$FULL_PATH_SEEDS/$modes_info/
                CURRENT_PATH_SCOPE=$FULL_PATH_SCOPE/$modes_info/
                python ../10_1_scope_analyse.py ${CURRENT_SPECIES} "${SBML_DIR}/${CURRENT_FILE}" ${CURRENT_PATH_SCOPE} ${CURRENT_PATH_SEED} "${OBJECTIVE_DIR}/${CURRENT_SPECIES}_target.txt" ${modes_info}
            done
        done
    done
done

