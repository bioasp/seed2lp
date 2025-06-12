#!/bin/bash
#SBATCH --job-name=job_s2lp_com         # Job name
#SBATCH --output=../output/s2lp_com/s2lp-%A_%a.out
#SBATCH -e ../error/s2lp_com/s2lp-%A_%a.err
#SBATCH --ntasks-per-node=1             #Number of tasks per node
#SBATCH --mem-per-cpu=50gb
#SBATCH --time=72:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01

source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lpcom

COM_DIR="../../results_communities"
DIR_NAME_NOLIM="more_less_rejected_nolimtransf_15min_results"
DIR_NAME_LIM6="more_less_rejected_limtransf6_15min_results"
DIR_NAME_LIM12="more_less_rejected_limtransf12_15min_results"

RESULT_NOLIM_DIR="${COM_DIR}/${DIR_NAME_NOLIM}/"
RESULT6_DIR="${COM_DIR}/${DIR_NAME_LIM6}/"
RESULT12_DIR="${COM_DIR}/${DIR_NAME_LIM12}/"

TEMP1_DIR=../../tmp7/
TEMP2_DIR=../../tmp8/
TEMP3_DIR=../../tmp9/


########## EXECUTE COMMUNITY ##########

########################
##  no limit transfer ##
########################


# # GLOBAL
# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c global -f com_less_rejected.txt -s reasoning -d $RESULT_NOLIM_DIR -t 15 -b $TEMP1_DIR
# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c global -f com_less_rejected.txt -s filter -d $RESULT_NOLIM_DIR -t 15 -b $TEMP1_DIR

# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c global -f com_more_rejected.txt -s reasoning -d $RESULT_NOLIM_DIR -t 15 -b $TEMP1_DIR
# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c global -f com_more_rejected.txt -s filter -d $RESULT_NOLIM_DIR -t 15 -b $TEMP1_DIR


# BISTEPS
# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c bisteps -f com_less_rejected.txt -s reasoning -d $RESULT_NOLIM_DIR -t 15 -b $TEMP1_DIR
# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c bisteps -f com_less_rejected.txt -s filter -d $RESULT_NOLIM_DIR -t 15 -b $TEMP1_DIR

# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c bisteps -f com_more_rejected.txt -s reasoning -d $RESULT_NOLIM_DIR -t 15 -b $TEMP1_DIR
# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c bisteps -f com_more_rejected.txt -s filter -d $RESULT_NOLIM_DIR -t 15 -b $TEMP1_DIR


# DELSUPSET FULL VERSION
# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c delsupset -f com_less_rejected.txt -s reasoning -d $RESULT_NOLIM_DIR -t 15 -b $TEMP1_DIR
# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c delsupset -f com_less_rejected.txt -s filter -d $RESULT_NOLIM_DIR -t 15 -b $TEMP1_DIR

# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c delsupset -f com_more_rejected.txt -s reasoning -d $RESULT_NOLIM_DIR -t 15 -b $TEMP1_DIR
# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c delsupset -f com_more_rejected.txt -s filter -d $RESULT_NOLIM_DIR -t 15 -b $TEMP1_DIR


# ########################
# ### limit transfer 6 ###
# ########################

# # GLOBAL
# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c global -f com_less_rejected.txt -s reasoning -d $RESULT6_DIR -l 6 -t 15 -b $TEMP2_DIR
# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c global -f com_less_rejected.txt -s filter -d $RESULT6_DIR -l 6 -t 15 -b $TEMP2_DIR

# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c global -f com_more_rejected.txt -s reasoning -d $RESULT6_DIR -l 6 -t 15 -b $TEMP2_DIR
# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c global -f com_more_rejected.txt -s filter -d $RESULT6_DIR -l 6 -t 15 -b $TEMP2_DIR

# BISTEPS
# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c bisteps -f com_less_rejected.txt -s reasoning -d $RESULT6_DIR -l 6 -t 15 -b $TEMP2_DIR
# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c bisteps -f com_less_rejected.txt -s filter -d $RESULT6_DIR -l 6 -t 15 -b $TEMP2_DIR

# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c bisteps -f com_more_rejected.txt -s reasoning -d $RESULT6_DIR -l 6 -t 15 -b $TEMP2_DIR
# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c bisteps -f com_more_rejected.txt -s filter -d $RESULT6_DIR -l 6 -t 15 -b $TEMP2_DIR

# DELSUPSET FULL VERSION
# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c delsupset -f com_less_rejected.txt -s reasoning -d $RESULT6_DIR -l 6 -t 15 -b $TEMP2_DIR
# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c delsupset -f com_less_rejected.txt -s filter -d $RESULT6_DIR -l 6 -t 15 -b $TEMP2_DIR

# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c delsupset -f com_more_rejected.txt -s reasoning -d $RESULT6_DIR -l 6 -t 15 -b $TEMP2_DIR
# sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c delsupset -f com_more_rejected.txt -s filter -d $RESULT6_DIR -l 6 -t 15 -b $TEMP2_DIR



########################
## limit transfer 12 ###
########################

# GLOBAL
#sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c global -f com_less_rejected.txt -s reasoning -d $RESULT12_DIR -l 12 -t 15 -b $TEMP3_DIR
#sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c global -f com_less_rejected.txt -s filter -d $RESULT12_DIR -l 12 -t 15 -b $TEMP3_DIR

#sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c global -f com_more_rejected.txt -s reasoning -d $RESULT12_DIR -l 12 -t 15 -b $TEMP3_DIR
#sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c global -f com_more_rejected.txt -s filter -d $RESULT12_DIR -l 12 -t 15 -b $TEMP3_DIR


# BISTEPS
sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c bisteps -f com_less_rejected.txt -s reasoning -d $RESULT12_DIR -l 12 -t 15 -b $TEMP3_DIR
sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c bisteps -f com_less_rejected.txt -s filter -d $RESULT12_DIR -l 12 -t 15 -b $TEMP3_DIR

#sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c bisteps -f com_more_rejected.txt -s reasoning -d $RESULT12_DIR -l 12 -t 15 -b $TEMP3_DIR
#sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c bisteps -f com_more_rejected.txt -s filter -d $RESULT12_DIR -l 12 -t 15 -b $TEMP3_DIR


# DELSUPSET FULL VERSION
#sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c delsupset -f com_less_rejected.txt -s reasoning -d $RESULT12_DIR -l 12 -t 15 -b $TEMP3_DIR
#sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c delsupset -f com_less_rejected.txt -s filter -d $RESULT12_DIR -l 12 -t 15 -b $TEMP3_DIR

#sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c delsupset -f com_more_rejected.txt -s reasoning -d $RESULT12_DIR -l 12 -t 15 -b $TEMP3_DIR
#sbatch 15_0_job_run_s2lp_com_less_more_rejected.sh -c delsupset -f com_more_rejected.txt -s filter -d $RESULT12_DIR -l 12 -t 15 -b $TEMP3_DIR