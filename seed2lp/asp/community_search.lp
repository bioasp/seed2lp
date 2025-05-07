%%%%%%%%%%%%%%%%%%%%%%% COMMUNITY METABOLITES ACTIVATION %%%%%%%%%%%%%%%%%%%%%%%
%*
A metabolite is activated by transfer between networks.
We choose the transferred metabolites that needed to be activate.
*%
{transferred(N,B1,B2,M1,M2)} :- activated(M1), metabolite(M1,_,N,B1), metabolite(M2,_,N,B2),
                        B1 != B2, B1 != "pool", B2 != "pool"; 
                        not seed(M1,_,N,_), not transported_meta(M1).
activated(M) :- metabolite(M,_,N,B2), transferred(N,B1,B2,_,_).

% Contraintes a rajouté a partir du fichier de forbidden transfers rajouté a l'init dans l'instance
% :- transferred()
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

