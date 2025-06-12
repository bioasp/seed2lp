#!/bin/bash
#SBATCH --job-name=bigg_check_flux         # Job name
#SBATCH --output=../output/s2lp_com/bigg_check_flux-%A_%a.out
#SBATCH -e ../error/s2lp_com/bigg_check_flux-%A_%a.err
#SBATCH --cpus-per-task=10                          #Request that ncpus be allocated per process.
#SBATCH --ntasks-per-node=1                         #Number of tasks per node
#SBATCH --mem-per-cpu=50gb
#SBATCH --time=72:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01
#SBATCH -C diablo

########## SERVER ##########
COM_DIR="../../networks"
DESC_DIR="${COM_DIR}/description"
XML_DIR="${COM_DIR}/xml"
############################

########### LOCAL ##########
#COM_DIR="../../analyses_com/data"
#DESC_DIR="${COM_DIR}/descriptions"
#XML_DIR="${COM_DIR}/xml"
############################

while getopts c:d:o:m:q: flag
do
    case "${flag}" in
        c) COM_NAME=${OPTARG};;
        d) RESULT_DIR=${OPTARG};;
        o) OUTPUT_DIR=${OPTARG};;
        m) MODE=${OPTARG};;
        q)
          if [[ -n ${OPTARG} ]]; then
              EQ_FLUX=${OPTARG}
          fi
        ;;

    esac
done


COM_PATH="${DESC_DIR}/${COM_NAME}.txt"

#COMPLEMENT_ARG="-fp 10 "
COMPLEMENT_ARG=""


# Create directories if needed
if [[ ! -d "$OUTPUT_DIR" ]]
then
  mkdir -p "$OUTPUT_DIR"
fi

if [[ ! -d "$OUTPUT_DIR/logs" ]]
then
  mkdir -p "$OUTPUT_DIR/logs"
fi



# if argument not empty
if [[ -n ${EQ_FLUX} ]]; then
  COMPLEMENT_ARG=$COMPLEMENT_ARG"-ef "
fi


file_list=$(find "$RESULT_DIR/"/ -maxdepth 1 -mindepth 1 -type f  -name "${COM_NAME}_*${MODE}*_taf_reas_no_accu_results.json" -print)

for file in  $file_list
do  
  RESULT_FILE=$file

  #echo "seed2lp fluxcom $COM_PATH $XML_DIR $RESULT_FILE $OUTPUT_DIR $COMPLEMENT_ARG"
  seed2lp fluxcom $COM_PATH $XML_DIR $RESULT_FILE $OUTPUT_DIR $COMPLEMENT_ARG
done



