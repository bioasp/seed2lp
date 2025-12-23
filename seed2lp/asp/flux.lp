%metabolite(M,X) :- reactant(M,_,_,X).
%metabolite(M,X) :- product(M,_,_,X).  

%%%%%%%%%%%%%%%%%%% IMPORTING SINK METABOLITES %%%%%%%%%%%%%%%%%%%%
% Create import reactions for seeds not taggued as exchange
% (meaning to involved in exchange reaction)
% First create an import reaction forward with reactant 
reac_import(M) :- seed(M,X,N,B), X!="exchange".
reaction(reac_import(M)) :- reac_import(M).
product(M,"1.0000",reac_import(M),X,N,B) :- reac_import(M), seed(M,X,N,B).
bounds(reac_import(M),"0","1000") :- reac_import(M).

% Because we are adding an import reaction reaction, this reaction become an exchange
% reaction and has to be tggued as exchange for seed_external definition
exchange(reac_import(M)) :- reac_import(M).

% then create the export reaction
reac_export(M) :- seed(M,X,N,B), X!="exchange".
reaction(reac_export(M)) :- reac_export(M).
reactant(M,"1.0000",reac_export(M),X,N,B) :- reac_export(M), seed(M,X,N,B).
bounds(reac_export(M),"0","1000") :- reac_export(M).
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


%%%%%%%%%%%%%%%%%%%% IMPORTING EXCHANGE METABOLITES %%%%%%%%%%%%%%%%%%%%
% add the reverse of an already existing exchange reaction 
% in order to do that, we need to create a reaction having the metabolite in product
% we do that only if we remove import reaction and though the reversible does not exist
% we do it only for reaction that are also exchange reaction
% the boundary is [0,1000] because the forward reaction already exists
import_exch(R) :- seed(M,"exchange",N,B), rm_product(M,_,R,"exchange",_,B).
reaction(R) :- import_exch(R).
product(M,S,R,X,N,B) :- rm_product(M,S,R,X,N,B), import_exch(R).
bounds(R,"0","1000") :- import_exch(R).

% if the sbml doesn't have an exchange reaction reversible, it is possible to have 
% only the export reaction written and not the import, so there is no atom rm_product
% or rm_reaction. So we create from scratch this import reaction for an exchange metabolite
import_exch_created(M,B) :- seed(M,"exchange",N,B), not rm_product(M,_,_,"exchange",_,_).
reaction(import_exch_created(B)) :- import_exch_created(M,B).
product(M,"1.0000",import_exch_created(M),"exchange",M,B) :- import_exch_created(M,B).
bounds(import_exch_created(M),"0","1000") :- import_exch_created(M,B).

% if the sbml doesn't have an exchange reaction reversible, it is possible to have 
% only the import reaction written and not the export, so there is an atom rm_product
% for an exchange reaction, but the reversible doesn't exist.
% We create an export reaction
export_exch_created(M,B) :- seed(M,"exchange",N,B), rm_product(M,_,R,"exchange",_,_), exchange(R),
                         not reversible(R,_), not reversible(_,R).
reaction(export_exch_created(M)) :- export_exch_created(M,B).
reactant(M,"1.0000",export_exch_created(M),"exchange",M,B) :- export_exch_created(M,B).
bounds(export_exch_created(M),"0","1000") :- export_exch_created(M,B).
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


%%%%%%%%%%%%%%%%%%%%%%% FLUX BALANCE ANALYSIS DEFINITION %%%%%%%%%%%%%%%%%%%%%%%%
% domain definition; default dom{(x,0,inf)}
&dom{L..U} = R :- bounds(R,L,U), reaction(R).

% FBA definition
%OS: Product stoicihiometry by producting reaction OR
%IS: Consumed stoichiometry by consuming reaction IR

&sum{ OS*OR   : reactant(M,OS,OR,_,_,_);
    -IS*IR   : product(M,IS,IR,_,_,_)
    } = 0 :- metabolite(M,_,_,_).

% goal condition: target flux > 0
&sum{ R :objective(R) } >= "0.0001".
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%