#!/bin/bash
#SBATCH --job-name=job_s2lp         # Job name
#SBATCH --output=../output/workflow/s2lp-%A_%a.out
#SBATCH -e ../error/workflow/s2lp-%A_%a.err
#SBATCH --mem-per-cpu=10gb
#SBATCH --ntasks-per-node=1             #Number of tasks per node
#SBATCH --time=72:00:00                 # Time limit hrs:min:sec
#SBATCH --mail-user=chabname.ghassemi-nedjad@inria.fr         #Receive email on this adress when the job is begin,over,or fail 
#SBATCH --mail-type=END,FAIL                  #Define what we want to receive by email about the job statut
#SBATCH --exclude=arm01

source /home/cghassem/miniconda3/etc/profile.d/conda.sh
conda activate s2lp

# Cluster
FILE="03_02_job_run_s2lp_exclusive"
###### EXECUTE FULL NETWORK #######

### SPECIFIC ###
sbatch $FILE -c full -m m -s hybrid

sbatch $FILE -c full -m m -s hybrid -a a
###################################

########## EXECUTE TARGET ##########


### SPECIFIC ###
sbatch $FILE -c target -m m -s hybrid


sbatch $FILE -c target -m m -s hybrid -a a
###################################

########## EXECUTE FBA ##########
 sbatch $FILE -c fba -m m 
