#!/bin/bash
#SBATCH --job-name=job_s2lp_com       # Job name
#SBATCH --output=../output/s2lp_com/metabolites-%A_%a.out
#SBATCH -e ../error/s2lp_com/metabolites-%A_%a.err
#SBATCH --cpus-per-task=1                          #Request that ncpus be allocated per process.
#SBATCH --ntasks-per-node=1                         #Number of tasks per node
#SBATCH --time=72:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01


source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lp


S2LP_RESULT_DIR="../../networks/communities/results/e_coli_core"
ECOLI_FILE="../../analyses/data/bigg/sbml/e_coli_core.xml"
META_RESULT_DIR="../../networks/communities/results/e_coli_core_meta"

python ../13_1_com_e_coli_core_metabolite_analyses.py $S2LP_RESULT_DIR $ECOLI_FILE $META_RESULT_DIR "e_coli_core_2_1"
python ../13_1_com_e_coli_core_metabolite_analyses.py $S2LP_RESULT_DIR $ECOLI_FILE $META_RESULT_DIR "e_coli_core_2_2"
python ../13_1_com_e_coli_core_metabolite_analyses.py $S2LP_RESULT_DIR $ECOLI_FILE $META_RESULT_DIR "e_coli_core_2_3"
python ../13_1_com_e_coli_core_metabolite_analyses.py $S2LP_RESULT_DIR $ECOLI_FILE $META_RESULT_DIR "e_coli_core_3"
