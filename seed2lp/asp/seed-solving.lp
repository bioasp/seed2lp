% Search of the minimal set of seeds in all graph activating all targets or specific targets.
% The 
%
% INPUTS:
%   - seed_user(S): node S is a seed given by users
%   - forbidden(S): node S cannot be a seed
%   - target(T): node T must be activated
%   - reaction(R): R is a reaction.
%   - reactant(T,_,R,_): T is a reactant of reaction R.
%   - product(P,_,R,_): P is a product of reaction R.
% OUTPUTS:  one model for each set of seed that activate all metabolites
%   - seed(S,_): node S is a seed
#const run_mode=target. % full/target/fba
#const accu=0.
#const subseed=0. % mode select sub seed amoung possible seeds given by user

% A metabolite is a reactant or product.
metabolite(M,X) :- reactant(M,_,_,X).
metabolite(M,X) :- product(M,_,_,X).                   


%%%%%%%%%%%%%%%%%%%%%%%%%%%%% INITIAL COMPUTATION %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% An initial seed is activated    
activated_initial(S) :- seed_user(S).    
activated_initial(S) :- seed_external(S).
                                  
% Compute the initial scope from intial seeds                 
activated_initial(M) :- metabolite(M,_) ; product(M,_,R,_) ;        
                        activated_initial(T): reactant(T,_,R,_);
                        % We reject de reaction created for flux mode to not have
                        % as activated initial the seed and the reaction
                        % can creates problems for cycles
                        not reac_import(M), not reac_export(M),
                        not import_exch(R), not import_exch_created(M), not export_exch_created(M).  

        
% Define which non exchange metabolite is an imported metabolite
% meaning, there is a reation that transport the metabolite frome extracellular (tagued exchange)
% into intracellular (tagued other)
transported_meta(M) :- product(M,_,_,"transport").
transported_meta(M) :- reactant(M,_,_,"transport").
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
                                  
%%%%%%%%%%%%%%%%%%%%%%% POSSIBLE SEEDS WHEN GIVEN BY USER %%%%%%%%%%%%%%%%%%%%%%% 
% When user gives a file of possible seeds, we want to find a subset of this seeds
% that respects the constraints (in any mode) 
p_seed(M) :- sub_seed(M), subseed=1.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


%%%%%%%%%%%%%%%%%%%%%%%%% TARGET SPECIFIC SEEDS SEARCH %%%%%%%%%%%%%%%%%%%%%%%%%                               
% Try to cut the set of possible seeds   
can_reach(M) :- target(M) ; run_mode=target, subseed=0.                    
can_reach(M) :- reactant(M,_,R,_) ; product(P,_,R,_) ; can_reach(P) ; run_mode=target, subseed=0.    

% Possible seed detection when the user do not give them

% Determine possible seeds when accumulation allowed
% Eliminate the metabolite imported (having an import reaction)
% Eliminate for example all the combination :
% M_S1_e, M_S2_e, M_S3_e with M_S1_C, M_S2_c, M_S3_c
% keep only M_S1_e, M_S2_e, M_S3_e
p_seed(M) :- can_reach(M), metabolite(M,_), not seed_user(M),
            not transported_meta(M); 
            run_mode=target, accu=1, subseed=0.
              

% Case accumulation not allowed, we need to reach more metabolite
% to access to solution without accumulation
p_seed(M) :- metabolite(M,_), not seed_user(M), 
            not transported_meta(M); 
            run_mode=target, accu=0, subseed=0.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%%% FULL NETWORK SEEDS SEARCH %%%%%%%%%%%%%%%%%%%%%%%%%%    
% A metabolite which is not a product of any reaction except
% except his own exchange reaction is an external seed and must be a seed
% when the search is full network
% Also there is some cases when we have a reaction reversible where there is no
% exchange reaction. Such as B_m <-> B_c, then None -> A_c and B_c + A_c -> C_c
% We need to select one of the metabolite B as seed, but because of the reversibility
% it is not selected if we don't take the reversible reaction into account.
seed_external(M) :- reactant(M,_,_,_), 
                    not product(M,_,R,_): reaction(R), 
                    not exchange(R), not reversible(_,R);
                    not transported_meta(M);
                    run_mode=full, subseed=0.
seed_external(M) :- reactant(M,_,_,_), 
                    not product(M,_,R,_): reaction(R), 
                    not exchange(R), not reversible(R,_);
                    not transported_meta(M);
                    run_mode=full, subseed=0.

% A metabolite which is only product of reaction cannot be a seed         
impossible_seed(M) :- product(M,_,_,_) ; not reactant(M,_,_,_) ; run_mode=full, subseed=0.   
                                  
target(M) :- metabolite(M,_) ; run_mode=full.                   
                                  
% Determine possible seeds all the time (with or without accumulation)
p_seed(M) :- metabolite(M,_); not transported_meta(M) ; 
            not impossible_seed(M) ; not activated_initial(M) ; 
            run_mode=full, subseed=0. 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% FBA SEEDS SEARCH %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%  
% Determine possible seeds for FBA : All metabolites are possible seeds
% Randomly choose metabolites, excepts the metabolite that are never consumed
% otherwise the flux will create an import/Export reaction to avoid accumulation
p_seed(M) :- metabolite(M,_), not transported_meta(M), 
            not activated_initial(M), not authorized_accu(M), 
            run_mode=fba, subseed=0. 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


%%%%%%%%%%%%%%%%%%%%%%%%%%%%% SCOPE DETERMINATION %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% A metabolite is activated if produced by a reaction 
% with all its reactants activated.
activated(M) :- activated_initial(M).
activated(S) :- new_seed(S).

scopeR(R) :- reaction(R) ; activated(M): reactant(M,_,R,_).
activated(M) :- product(M,_,R,_) ; scopeR(R).
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% ACCUMULATION %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Avoid metabolite accumulation for target and full network mode
% The authorized accumulation of metabolites are for compounds that are never
% consumed by any reaction in the sbml file
% If FBA mode, all compounds are allowed to be accumulated, the fba will select
% the model without accumulation by itself with flux calculation
authorized_accu(M) :- product(M,_,_,_), not reactant(M,_,R,_): reaction(R), 
                      R != reac_export(M), R!= export_exch_created(M).

% Consumed at least one time
%%%%%%% TARGET OR FULL NETWORK %%%%%
% Target or Full mode, when accumulation not allowed
is_conso(M) :- reactant(M,_,R,_), scopeR(R), activated(M), accu=0, 
                R != reac_export(M), R!= export_exch_created(M); run_mode!=fba.
:- product(M,_,R,_), activated(M), not is_conso(M), 
    accu=0, not authorized_accu(M),  run_mode!=fba.


%%%%%%% FBA %%%%%
% FBA mode, for checking if a seed is here to create export reaction and avoid
% accumulation
is_conso(M) :- reactant(M,_,R,_), scopeR(R), activated(M), 
                R != reac_export(M), R!= export_exch_created(M); run_mode=fba.
seed_accu(M) :- not is_conso(M), seed(M,_); run_mode=fba.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%



%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% SEED SELECTION %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Choose a set of seed from the possible seeds
{ new_seed(M): p_seed(M), not forbidden(M) }.

% Discard any model that is not activating all targets when not possible seeds 
% given by the user.
:- target(M) ; not activated(M), run_mode!=fba, subseed=0.


% A seed is a seed given by the user, or an external seed 
% or a new seed coming from the combinations of possible seeds 
seed(M,X) :- seed_user(M), metabolite(M,X).
seed(M,X) :- seed_external(M), metabolite(M,X).
seed(M,X) :- new_seed(M), metabolite(M,X).
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#show seed/2.
#show seed_accu/1.