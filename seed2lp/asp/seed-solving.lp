%* 
Search of the minimal set of seeds in all graph activating all targets or specific targets.

INPUTS:
  - seed_user(S): node S is a seed given by users
  - forbidden(S): node S cannot be a seed
  - target(T): node T must be activated
  - reaction(R): R is a reaction.
  - reactant(T,_,R,_): T is a reactant of reaction R.
  - product(P,_,R,_): P is a product of reaction R.

OUTPUTS:  one model for each set of seed that activate all metabolites
  - seed(S,_): node S is a seed
*%
%#const run_mode=target. % full/target/fba % Defined in definition_atoms
%#const accu=0. % Defined in definition_atoms
%#const subseed=0. % Defined in definition_atoms


                                  
%%%%%%%%%%%%%%%%%%%%%%% POSSIBLE SEEDS WHEN GIVEN BY USER %%%%%%%%%%%%%%%%%%%%%%% 
%*
When user gives a file of possible seeds, we want to find a subset of this seeds
that respects the constraints (in any mode) 
*%
p_seed(M,N) :- sub_seed(N), metabolite(M,_,N,_), subseed=1.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


%%%%%%%%%%%%%%%%%%%%%%%%% TARGET SPECIFIC SEEDS SEARCH %%%%%%%%%%%%%%%%%%%%%%%%%                               
% Try to cut the set of possible seeds   
can_reach(N) :- target(N,M), metabolite(M,_,N,_); run_mode=target, subseed=0,  accu=1.                   
can_reach(N) :- reactant(M,_,R,_,N,_) ; product(P,_,R,_,O,_) ; can_reach(O) ; 
                run_mode=target, subseed=0, accu=1.

%*
Possible seed detection when the user do not give them:
Determine possible seeds when accumulation allowed
Eliminate the metabolite imported (having an import reaction)
Eliminate for example all the combination :
M_S1_e, M_S2_e, M_S3_e with M_S1_C, M_S2_c, M_S3_c
keep only M_S1_e, M_S2_e, M_S3_e
*%
p_seed(M,N) :- can_reach(N), metabolite(M,_,N,_), not seed_user(M),
            not transported_meta(M); 
            run_mode=target, accu=1, subseed=0.
              

%*
Case accumulation not allowed, we need to reach more metabolite
to access to solution without accumulation
*%
p_seed(M,N) :- metabolite(M,_,N,_), not seed_user(M), 
            not transported_meta(M); 
            run_mode=target, accu=0, subseed=0.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%%% FULL NETWORK SEEDS SEARCH %%%%%%%%%%%%%%%%%%%%%%%%%%    
%*
A metabolite which is not a product of any reaction except
except his own exchange reaction is an external seed and must be a seed
when the search is full network
Also there is some cases when we have a reaction reversible where there is no
exchange reaction. Such as B_m <-> B_c, then None -> A_c and B_c + A_c -> C_c
We need to select one of the metabolite B as seed, but because of the reversibility
it is not selected if we don't take the reversible reaction into account.
*%
seed_external(M) :- reactant(M,_,_,_,_,_), 
                    not product(M,_,R,_,_,_): reaction(R), 
                    not exchange(R), not reversible(_,R);
                    not transported_meta(M);
                    run_mode=full, subseed=0.
seed_external(M) :- reactant(M,_,_,_,_,_), 
                    not product(M,_,R,_,_,_): reaction(R), 
                    not exchange(R), not reversible(R,_);
                    not transported_meta(M);
                    run_mode=full, subseed=0.

% A metabolite which is only product of reaction cannot be a seed         
impossible_seed(M) :- product(M,_,_,_,_,_) ; not reactant(M,_,_,_,_,_) ; run_mode=full, subseed=0.   
                                  
target(N,M) :- metabolite(M,_,N,_) ; run_mode=full.                   
                                  
% Determine possible seeds all the time (with or without accumulation)
p_seed(M,N) :- metabolite(M,_,N,_); not transported_meta(M) ; 
            not impossible_seed(M) ; not activated_initial(M) ; 
            run_mode=full, subseed=0. 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% FBA SEEDS SEARCH %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%  
%*
Determine possible seeds for FBA : All metabolites are possible seeds
Randomly choose metabolites, excepts the metabolite that are never consumed
otherwise the flux will create an import/Export reaction to avoid accumulation
*%
p_seed(M,N) :- metabolite(M,_,N,_), not transported_meta(M), 
            not activated_initial(M), not authorized_accu(M), 
            run_mode=fba, subseed=0. 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%




%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% SEED SELECTION %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Choose a set of seed from the possible seeds
{ new_seed(M): p_seed(M,N), not forbidden(N) }.


% A seed is a seed given by the user, or an external seed 
% or a new seed coming from the combinations of possible seeds 
seed(M,X,N,B) :- seed_user(M), metabolite(M,X,N,B).
seed(M,X,N,B) :- seed_external(M), metabolite(M,X,N,B).
seed(M,X,N,B) :- new_seed(M), metabolite(M,X,N,B).
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
