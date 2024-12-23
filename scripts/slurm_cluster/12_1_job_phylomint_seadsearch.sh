#!/bin/bash
#SBATCH --job-name=job_phylomint         # Job name
#SBATCH --output=../output/phylomint/phylomint-%A_%a.out
#SBATCH -e ../error/phylomint/phylomint-%A_%a.err
#SBATCH --cpus-per-task=1                          #Request that ncpus be allocated per process.
#SBATCH --ntasks-per-node=1                         #Number of tasks per node
#SBATCH --time=72:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01
#SBATCH --array=1-107%55                           #107 networks

source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lp

DATA_DIR="../../analyses/data"
OBJECTIVE_DIR="${DATA_DIR}/objective"
SBML_DIR="${DATA_DIR}/sbml_corrected"
RESULT_DIR="../../analyses/results/phylomint"


./12_1_run_phylomint_seadsearch.sh  -s $SBML_DIR -o $OBJECTIVE_DIR  -r $RESULT_DIR