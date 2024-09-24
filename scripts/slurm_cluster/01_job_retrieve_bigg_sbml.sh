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

source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lp

RESULT_DIR="../../data/"

# Cluster
python ../01_retrieve_bigg_sbml.py $RESULT_DIR

rm "${RESULT_DIR}/bigg/sbml/iAT_PLT_636.xml"