#!/bin/bash
#SBATCH --job-name=job_netseed         # Job name
#SBATCH --output=../output/netseed/netseed-%A_%a.out
#SBATCH -e ../error/netseed/netseed-%A_%a.err
#SBATCH --cpus-per-task=1                          #Request that ncpus be allocated per process.
#SBATCH --ntasks-per-node=1                         #Number of tasks per node
#SBATCH --time=24:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01
#SBATCH --array=1-107%55                           #108 networks


source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lp

DATA_DIR="../../data"
OBJECTIVE_DIR="${DATA_DIR}/objective"
SBML_DIR="${DATA_DIR}/bigg/sbml"
RESULT_DIR="../../results"
NETSEED_RESULT_DIR="${RESULT_DIR}/precursor"
NETSEED_FORM_RESULT_DIR="${RESULT_DIR}/precursor_formated_results"
TOOL="PRECURSOR"

./05_2_results.sh -i $NETSEED_RESULT_DIR -r $NETSEED_FORM_RESULT_DIR -o $OBJECTIVE_DIR -s $SBML_DIR $TOOL
