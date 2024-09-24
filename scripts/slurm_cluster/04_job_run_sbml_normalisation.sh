#!/bin/bash
#SBATCH --job-name=job_sbml_rewrite         # Job name
#SBATCH --output=../output/sbml_rewrite/sbml_rewrite-%A_%a.out
#SBATCH -e ../error/sbml_rewrite/sbml_rewrite-%A_%a.err
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
SBML_DIR="${DATA_DIR}/bigg/sbml"
NORM_SBML_DIR="${DATA_DIR}/sbml_corrected"

./04_run_sbml_normalisation.sh -i $SBML_DIR -r $NORM_SBML_DIR
