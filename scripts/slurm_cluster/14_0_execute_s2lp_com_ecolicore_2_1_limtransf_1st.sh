#!/bin/bash
#SBATCH --job-name=com_1st        # Job name
#SBATCH --output=../output/s2lp_com/s2lp-%A_%a.out
#SBATCH -e ../error/s2lp_com/s2lp-%A_%a.err
#SBATCH --ntasks-per-node=1             #Number of tasks per node
#SBATCH --mem-per-cpu=10gb
#SBATCH --time=72:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01

source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lpcom

COM_DIR="../../results_communities"
DIR_NAME="e_coli_core_2_1_limtransf2_1st_results"
RESULT_DIR="${COM_DIR}/${DIR_NAME}/"


########## EXECUTE COMMUNITY ##########
### 2 species ###
# GLOBAL
#sbatch 14_0_job_run_s2lp.sh -c global -f com_e_coli_core_2_1.txt -s reasoning -d $RESULT_DIR -t 60 -l 2 -n 1


# BISTEPS
#sbatch 14_0_job_run_s2lp.sh -c bisteps -f com_e_coli_core_2_1.txt -s reasoning -d $RESULT_DIR -t 60 -l 2 -n 1
#sbatch 14_0_job_run_s2lp.sh -c bisteps -f com_e_coli_core_2_1.txt -s reasoning -d $RESULT_DIR -t 60 -l 2 -n 1 -a a


# DELSUPSET FULL VERSION
sbatch 14_0_job_run_s2lp.sh -c delsupset -f com_e_coli_core_2_1.txt -s reasoning -d $RESULT_DIR -t 60 -l 2 -n 1
#sbatch 14_0_job_run_s2lp.sh -c delsupset -f com_e_coli_core_2_1.txt -s reasoning -d $RESULT_DIR -t 60 -l 2 -n 1 -a a
