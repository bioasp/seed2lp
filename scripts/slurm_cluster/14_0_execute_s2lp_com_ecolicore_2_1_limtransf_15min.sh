#!/bin/bash
#SBATCH --job-name=job_s2lp_com         # Job name
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
PARTIAL_DELSUPSET_COM_DIR="../../results_communities_pd"
DIR_NAME_LIM2="e_coli_core_2_1_limtransf2_15min_results"
DIR_NAME_LIM3="e_coli_core_2_1_limtransf3_15min_results"

RESULT2_DIR="${COM_DIR}/${DIR_NAME_LIM2}/"
RESULT2_DIR_PARTIAL_DELETE="${PARTIAL_DELSUPSET_COM_DIR}/${DIR_NAME_LIM2}/"

RESULT3_DIR="${COM_DIR}/${DIR_NAME_LIM3}/"
RESULT3_DIR_PARTIAL_DELETE="${PARTIAL_DELSUPSET_COM_DIR}/${DIR_NAME_LIM3}/"

TEMP1_DIR=../../tmp1/
TEMP2_DIR=../../tmp2/


########## EXECUTE COMMUNITY ##########

########################
### limit transfer 2 ###
########################

# GLOBAL
# sbatch 14_0_job_run_s2lp.sh -c global -f com_e_coli_core_2_1.txt -s reasoning -d $RESULT2_DIR -t 15 -l 2 -b $TEMP1_DIR


# # BISTEPS
# sbatch 14_0_job_run_s2lp.sh -c bisteps -f com_e_coli_core_2_1.txt -s reasoning -d $RESULT2_DIR -t 15 -l 2 -b $TEMP1_DIR
# sbatch 14_0_job_run_s2lp.sh -c bisteps -f com_e_coli_core_2_1.txt -s reasoning -d $RESULT2_DIR -t 15 -l 2 -a a -b $TEMP1_DIR


# DELSUPSET FULL VERSION
sbatch 14_0_job_run_s2lp.sh -c delsupset -f com_e_coli_core_2_1.txt -s reasoning -d $RESULT2_DIR -t 15 -l 2 -b $TEMP1_DIR
# sbatch 14_0_job_run_s2lp.sh -c delsupset -f com_e_coli_core_2_1.txt -s reasoning -d $RESULT2_DIR -t 15 -l 2 -a a -b $TEMP1_DIR

# DELSUPSET PARTIAL VERSION
# sbatch 14_0_job_run_s2lp.sh -c delsupset -f com_e_coli_core_2_1.txt -s reasoning -d $RESULT2_DIR_PARTIAL_DELETE -t 15 -l 2 -p p -b $TEMP1_DIR
# sbatch 14_0_job_run_s2lp.sh -c delsupset -f com_e_coli_core_2_1.txt -s reasoning -d $RESULT2_DIR_PARTIAL_DELETE -t 15 -l 2 -p p -a a -b $TEMP1_DIR


########################
### limit transfer 3 ###
########################
# GLOBAL
# sbatch 14_0_job_run_s2lp.sh -c global -f com_e_coli_core_2_1.txt -s reasoning -d $RESULT3_DIR -t 15 -l 3 -b $TEMP2_DIR


# # BISTEPS
# sbatch 14_0_job_run_s2lp.sh -c bisteps -f com_e_coli_core_2_1.txt -s reasoning -d $RESULT3_DIR -t 15 -l 3 -b $TEMP2_DIR
# sbatch 14_0_job_run_s2lp.sh -c bisteps -f com_e_coli_core_2_1.txt -s reasoning -d $RESULT3_DIR -t 15 -l 3 -a a -b $TEMP2_DIR


# DELSUPSET FULL VERSION
# sbatch 14_0_job_run_s2lp.sh -c delsupset -f com_e_coli_core_2_1.txt -s reasoning -d $RESULT3_DIR -t 15 -l 3 -b $TEMP2_DIR
# sbatch 14_0_job_run_s2lp.sh -c delsupset -f com_e_coli_core_2_1.txt -s reasoning -d $RESULT3_DIR -t 15 -l 3 -a a -b $TEMP2_DIR

# # DELSUPSET PARTIAL VERSION
# sbatch 14_0_job_run_s2lp.sh -c delsupset -f com_e_coli_core_2_1.txt -s reasoning -d $RESULT3_DIR_PARTIAL_DELETE -t 15 -l 3 -p p -b $TEMP2_DIR
# sbatch 14_0_job_run_s2lp.sh -c delsupset -f com_e_coli_core_2_1.txt -s reasoning -d $RESULT3_DIR_PARTIAL_DELETE -t 15 -l 3 -p p -a a -b $TEMP2_DIR