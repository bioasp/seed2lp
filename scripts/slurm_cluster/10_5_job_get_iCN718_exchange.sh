#!/bin/bash
#SBATCH --job-name=job_timers         # Job name
#SBATCH --output=../output/timers/timers-%A_%a.out
#SBATCH -e ../error/timers/timers-%A_%a.err
#SBATCH #SBATCH --nodes=1                                   #Number of nodes    
#SBATCH --cpus-per-task=1                          #Request that ncpus be allocated per process.
#SBATCH --mem-per-cpu=10gb
#SBATCH --ntasks-per-node=1                         #Number of tasks per node
#SBATCH --time=10:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01


source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lp

DATA_DIR="../../data"
SBML_DIR="${DATA_DIR}/bigg/sbml"
SPECIES="iCN718"
SBML_FILE="${SBML_DIR}/${SPECIES}.xml"
RESULT_DIR="../../results"
OUT_DIR="${RESULT_DIR}/metabolites_${SPECIES}"

# SERVER
python ../10_5_get_exchange.py $SPECIES $SBML_FILE $OUT_DIR
