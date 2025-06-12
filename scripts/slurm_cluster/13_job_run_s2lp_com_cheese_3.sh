#!/bin/bash
#SBATCH --job-name=job_s2lp         # Job name
#SBATCH --output=../output/s2lp_com/s2lp-%A_%a.out
#SBATCH -e ../error/s2lp_com/s2lp-%A_%a.err
#SBATCH --cpus-per-task=1                          #Request that ncpus be allocated per process.
#SBATCH -C zonda
#SBATCH --ntasks-per-node=1                         #Number of tasks per node
#SBATCH --time=72:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01


source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lpcom

########## SERVER ##########
COM_DIR="../../networks/communities"
COM="${COM_DIR}/description/cheese.txt"
SBML_DIR="${COM_DIR}/sbml/"
RESULT_DIR="${COM_DIR}/results/cheese_3/"
TEMP_DIR="../../tmp/"

while getopts c:s: flag
do
    case "${flag}" in
        c) COM_MODE=${OPTARG};;
        s) 
          if [[ ! -z ${OPTARG} ]]; then
              SOLVE=${OPTARG}
          fi
        ;;
    esac
done

seed2lp community $COM $SBML_DIR $RESULT_DIR -cm $COM_MODE -tl 0 -nbs 1 -so $SOLVE -tmp $TEMP_DIR