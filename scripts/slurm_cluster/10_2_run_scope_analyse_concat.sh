#!/bin/bash

while getopts r: flag
do
    case "${flag}" in
        r) SCOPE_DIR=${OPTARG};;
        *) echo "Invalid OPTION" && exit 1;;
    esac
done

####################
###### SERVER ######
####################

first_line="\tspecies\trun\tmode\toptim\taccu\tmodel\tis_equal_union_species\tmissing\tpercentage_missing\tis_biomass_included\tmissing_biomass\tpercentage_missing_biomass\tis_exchange_included\tmissing_exchange\tpercentage_missing_exchange\tis_seed_included_to_exchange\tmissing_seed_into_exchange\tpercentage_missing_seed_into_exchange\tis_exchange_included_to_seed\tmissing_exchange_into_seed\tpercentage_missing_exchange_into_seeds"
for dir in $SCOPE_DIR/*
do
    CURRENT_SPECIES=$(basename "$dir" | sed 's/\.[^.]*$//')
    file_list=$(find "$SCOPE_DIR/$CURRENT_SPECIES/scope"/ -maxdepth 5 -mindepth 5 -type f  -name "*_compare.tsv" -print)

    echo -e $first_line >> $SCOPE_DIR/$CURRENT_SPECIES/"${CURRENT_SPECIES}_scope_compare.tsv"
    for i in  $file_list
    do 
        awk FNR!=1 $i >> $SCOPE_DIR/$CURRENT_SPECIES/"${CURRENT_SPECIES}_scope_compare.tsv"
        done
done
