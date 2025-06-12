# CHANGE THE PATHS TO YOUR RESULTS AND NETWORKS

NETWORK_DIR="../../analyses_com/data/toys"
COM_DESCRIPTION_DIR="../../analyses_com/data/descriptions"
RESULTS_DIR="../../analyses_com/results/com_toys"


############################################
################## GLOBAL ##################
############################################

# REASONING

seed2lp community $COM_DESCRIPTION_DIR/com2_1.txt $NETWORK_DIR $RESULTS_DIR -cm global -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_2.txt $NETWORK_DIR $RESULTS_DIR -cm global -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_3.txt $NETWORK_DIR $RESULTS_DIR -cm global -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_4.txt $NETWORK_DIR $RESULTS_DIR -cm global -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_5.txt $NETWORK_DIR $RESULTS_DIR -cm global -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_6.txt $NETWORK_DIR $RESULTS_DIR -cm global -so reasoning -nbs 0  -tmp tmp/

seed2lp community $COM_DESCRIPTION_DIR/com3_1.txt $NETWORK_DIR $RESULTS_DIR -cm global -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com3_2.txt $NETWORK_DIR $RESULTS_DIR -cm global -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com3_3.txt $NETWORK_DIR $RESULTS_DIR -cm global -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com3_4.txt $NETWORK_DIR $RESULTS_DIR -cm global -so reasoning -nbs 0  -tmp tmp/

seed2lp community $COM_DESCRIPTION_DIR/com4.txt   $NETWORK_DIR $RESULTS_DIR -cm global -so reasoning -nbs 0  -tmp tmp/


############################################

# FILTER EQUALITY FLUX

seed2lp community $COM_DESCRIPTION_DIR/com2_1.txt $NETWORK_DIR $RESULTS_DIR -cm global -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_2.txt $NETWORK_DIR $RESULTS_DIR -cm global -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_3.txt $NETWORK_DIR $RESULTS_DIR -cm global -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_4.txt $NETWORK_DIR $RESULTS_DIR -cm global -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_5.txt $NETWORK_DIR $RESULTS_DIR -cm global -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_6.txt $NETWORK_DIR $RESULTS_DIR -cm global -so filter -nbs 0 -ef -tmp tmp/

seed2lp community $COM_DESCRIPTION_DIR/com3_1.txt $NETWORK_DIR $RESULTS_DIR -cm global -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com3_2.txt $NETWORK_DIR $RESULTS_DIR -cm global -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com3_3.txt $NETWORK_DIR $RESULTS_DIR -cm global -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com3_4.txt $NETWORK_DIR $RESULTS_DIR -cm global -so filter -nbs 0 -ef -tmp tmp/

seed2lp community $COM_DESCRIPTION_DIR/com4.txt   $NETWORK_DIR $RESULTS_DIR -cm global -so filter -nbs 0 -ef -tmp tmp/

############################################
################# BISTEPS ##################
############################################

# REASONING

seed2lp community $COM_DESCRIPTION_DIR/com2_1.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_2.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_3.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_4.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_5.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_6.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so reasoning -nbs 0  -tmp tmp/

seed2lp community $COM_DESCRIPTION_DIR/com3_1.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com3_2.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com3_3.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com3_4.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so reasoning -nbs 0  -tmp tmp/

seed2lp community $COM_DESCRIPTION_DIR/com4.txt   $NETWORK_DIR $RESULTS_DIR -cm bisteps -so reasoning -nbs 0  -tmp tmp/


############################################

# FILTER EQUALITY FLUX

seed2lp community $COM_DESCRIPTION_DIR/com2_1.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_2.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_3.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_4.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_5.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_6.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so filter -nbs 0 -ef -tmp tmp/

seed2lp community $COM_DESCRIPTION_DIR/com3_1.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com3_2.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com3_3.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com3_4.txt $NETWORK_DIR $RESULTS_DIR -cm bisteps -so filter -nbs 0 -ef -tmp tmp/

seed2lp community $COM_DESCRIPTION_DIR/com4.txt   $NETWORK_DIR $RESULTS_DIR -cm bisteps -so filter -nbs 0 -ef -tmp tmp/


############################################
################ DELSUPSET #################
############################################

# REASONING


seed2lp community $COM_DESCRIPTION_DIR/com2_1.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_2.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_3.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_4.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_5.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_6.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so reasoning -nbs 0  -tmp tmp/

seed2lp community $COM_DESCRIPTION_DIR/com3_1.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com3_2.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com3_3.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so reasoning -nbs 0  -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com3_4.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so reasoning -nbs 0  -tmp tmp/

seed2lp community $COM_DESCRIPTION_DIR/com4.txt   $NETWORK_DIR $RESULTS_DIR -cm delsupset -so reasoning -nbs 0  -tmp tmp/




############################################

# FILTER EQUALITY FLUX

seed2lp community $COM_DESCRIPTION_DIR/com2_1.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_2.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_3.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_4.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_5.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com2_6.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so filter -nbs 0 -ef -tmp tmp/

seed2lp community $COM_DESCRIPTION_DIR/com3_1.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com3_2.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com3_3.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so filter -nbs 0 -ef -tmp tmp/
seed2lp community $COM_DESCRIPTION_DIR/com3_4.txt $NETWORK_DIR $RESULTS_DIR -cm delsupset -so filter -nbs 0 -ef -tmp tmp/

seed2lp community $COM_DESCRIPTION_DIR/com4.txt   $NETWORK_DIR $RESULTS_DIR -cm delsupset -so filter -nbs 0 -ef -tmp tmp/
