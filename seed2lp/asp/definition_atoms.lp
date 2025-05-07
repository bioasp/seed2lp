#const subseed=0. % mode select sub seed amoung possible seeds given by user
#const run_mode=target. % full/target/fba
#const accu=0.

%*
A metabolite is a reactant or product.
M: Metabolite composed ID
X: Exchange tag of metabolite (exchange / transport / other / internal_exchange)
N: Metabolite Real ID
B: Species Name
*%
metabolite(M,X,N,B) :- reactant(M,_,_,X,N,B).
metabolite(M,X,N,B) :- product(M,_,_,X,N,B). 

%*
Define which non exchange metabolite is an imported metabolite
meaning, there is a reation that transport the metabolite frome extracellular (tagued exchange)
into intracellular (tagued other)
*%
transported_meta(M) :- product(M,_,_,"transport",_,_).
transported_meta(M) :- reactant(M,_,_,"transport",_,_).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%% INITIAL COMPUTATION %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% An initial seed is activated    
activated_initial(S) :- seed_user(S).    
activated_initial(S) :- seed_external(S).
                                  
% Compute the initial scope from intial seeds                 
activated_initial(M) :-  metabolite(M,_,_,_) ; product(M,_,R,_,_,_) ;        
                        activated_initial(T): reactant(T,_,R,_,_,_);
                        % We reject de reaction created for flux mode to not have
                        % as activated initial the seed and the reaction
                        % can creates problems for cycles
                        not reac_import(M), not reac_export(M),
                        not import_exch(R), not import_exch_created(M), not export_exch_created(M).  

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 


%%%%%%%%%%%%%%%%%%%% ACTIVATE METABOLITES %%%%%%%%%%%%%%%%%%%%%%%
activated(M) :- activated_initial(M).
activated(S) :- new_seed(S).
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%% SCOPE DETERMINATION %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%*
A metabolite is activated if produced by a reaction 
with all its reactants activated.
*%
scopeR(R) :- reaction(R) ; activated(M): reactant(M,_,R,_,_,_).
activated(M) :- product(M,_,R,_,_,_) ; scopeR(R).
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% ACCUMULATION %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%* 
Avoid metabolite accumulation for target and full network mode
The authorized accumulation of metabolites are for compounds that are never
consumed by any reaction in the sbml file
If FBA mode, all compounds are allowed to be accumulated, the fba will select
the model without accumulation by itself with flux calculation 
*%
authorized_accu(M) :- product(M,_,_,_,_,_), not reactant(M,_,R,_,_,_): reaction(R), 
                      R != reac_export(M), R!= export_exch_created(M).

%*
Consumed at least one time
%%%%%%% TARGET OR FULL NETWORK %%%%%%% 
Target or Full mode, when accumulation not allowed
*%
is_conso(M) :- reactant(M,_,R,_,_,_), scopeR(R), activated(M), accu=0, 
                R != reac_export(M), R!= export_exch_created(M); run_mode!=fba.
:- product(M,_,R,_,_,_), activated(M), not is_conso(M), 
    accu=0, not authorized_accu(M),  run_mode!=fba.


%*
%%%%%%% FBA %%%%%%% 
FBA mode, for checking if a seed is here to create export reaction and avoid
accumulation
*%
is_conso(M) :- reactant(M,_,R,_,_,_), scopeR(R), activated(M), 
                R != reac_export(M), R!= export_exch_created(M); run_mode=fba.
seed_accu(M) :- not is_conso(M), seed(M,_,_,_); run_mode=fba.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%