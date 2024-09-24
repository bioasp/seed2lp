% Enumeration of Connected Components.
% INPUTS:
%   - reaction(R): R is a reaction.
%   - reactant(T,R): T is a reactant of reaction R.
%   - product(P,R): P is a product of reaction R.
reaction(R) :- dreaction(R).
% OUTPUTS:
#show scc/2.      % nodes in each SCC
#show noinput/1.  % root SCC
#show sccedge/2.  % link between SCC


% the edges are linking reactants to products of each reaction.
oedge(T,P) :- reactant(T,R) ; product(P,R).

% the nodes
node(M) :- reactant(M,_).
node(M) :- product(M,_).

% #show oedge/2.
% #show node/1.


% recursive definition of link between nodes
link(A,B) :- oedge(A,B).
link(A,C) :- oedge(A,B) ; link(B,C).

% definitions of cycle
% A is in a cycle
cycle(A) :- link(A,A).
% A and B are in the same cycle
cycle(A,B) :- link(A,B) ; link(B,A) ; cycle(A) ; cycle(B) ; A<=B.

% defining strongly connected components (scc)
scc_(A,C) :- cycle(A,C) ; not cycle(B,A) : cycle(B), B<A.
% singleton scc
sscc(M) :- node(M) ; not scc_(_,M).


scc(A,A) :- sscc(A).
scc(A,C) :- scc_(A,C).


% link between SCCs A and B.
sccedge(A,B) :- oedge(Va, Vb) ; scc(A,Va) ; scc(B,Vb) ; A!=B.

% a scc without an incoming edge is a root.
noinput(A) :- sccedge(A,_) ; not sccedge(_,A).
% a scc without any edge to other scc is also a root.
noinput(A) :- scc(A,_) ; not sccedge(A,_) ; not sccedge(_,A).
