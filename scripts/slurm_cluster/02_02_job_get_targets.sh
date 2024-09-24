#!/bin/bash
#SBATCH --job-name=job_get_objective         # Job name
#SBATCH --output=../output/objective/objective-%A_%a.out
#SBATCH -e ../error/objective/objective-%A_%a.err
#SBATCH --cpus-per-task=1 # Request that ncpus be allocated per process.
#SBATCH --mem-per-cpu=10gb
#SBATCH --time=5:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01
#SBATCH --array=1-107%55                           #107 networks

source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lp

DATA_DIR="../../data"
SBML_DIR="${DATA_DIR}/bigg/sbml"
OBJECTIVE_DIR="${DATA_DIR}/objective"
TARGET_DIR="${DATA_DIR}/target"

# Cluster
sbattch ../02_02_get_targets.sh -s $SBML_DIR -o $OBJECTIVE_DIR -t $TARGET_DIR