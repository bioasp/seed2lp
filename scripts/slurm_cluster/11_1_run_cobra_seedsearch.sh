#!/bin/bash

# Get arguments
while getopts s:o:t:r:n: flag
do
    case "${flag}" in
        s) SBML_DIR=${OPTARG};;
        o) OBJECTIVE_DIR=${OPTARG};;
        t) TARGET_DIR=${OPTARG};;
        r) RESULT_DIR=${OPTARG};;
        n) NB_SOLUTION=${OPTARG};;
        *) echo "Invalid OPTION" && exit 1;;
    esac
done


for file in $(find  "$SBML_DIR"/ -maxdepth 1 -mindepth 1 -type f -print);
do
  CURRENT_SPECIES=$(basename $file | sed 's/\.[^.]*$//')
  echo $CURRENT_SPECIES
  PATH_TARGET=$TARGET_DIR/${CURRENT_SPECIES}_targets.txt
  PATH_OBJECTIVE=$OBJECTIVE_DIR/${CURRENT_SPECIES}_target.txt

  python ../11_1_cobra_seedsearch.py $file $PATH_TARGET $PATH_OBJECTIVE $RESULT_DIR $NB_SOLUTION
done