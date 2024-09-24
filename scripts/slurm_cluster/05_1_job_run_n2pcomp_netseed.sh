#!/bin/bash
#SBATCH --job-name=job_netseed         # Job name
#SBATCH --output=../output/netseed/netseed-%A_%a.out
#SBATCH -e ../error/netseed/netseed-%A_%a.err
#SBATCH -c 1                                        #Number of cores
#SBATCH --nodes=1                                   #Number of nodes    
#SBATCH --cpus-per-task=1                          #Request that ncpus be allocated per process.
#SBATCH --mem-per-cpu=10gb
#SBATCH --ntasks-per-node=1                         #Number of tasks per node
#SBATCH --time=1:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01


source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lp

DATA_DIR="../../data"
NORM_SBML_DIR="${DATA_DIR}/sbml_corrected"
N2PCOMP_DIR="../../N2PComp"
NETSEED_RESULT_DIR="../../results/netseed"
TOOL="NETSEED"

./05_1_run_n2pcom.sh -i $NORM_SBML_DIR  -n $N2PCOMP_DIR -r $NETSEED_RESULT_DIR -t $TOOL
