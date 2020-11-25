from proveit.basiclogic.boolean.theorems import orContradiction
from proveit.basiclogic import Implies, Not, Or, FALSE, inBool
from proveit.common import A, B

# (A or B) => FALSE assuming Not(A), Not(B)
orContradiction.instantiate().proven({Not(A), Not(B)})
# By contradiction: A assuming inBool(A), A or B, Not(B)
Implies(Not(A), FALSE).deriveViaContradiction().proven({inBool(A), Or(A, B), Not(B)})
# forall_{A, B | inBool(A), Not(B)} (A or B) => A
Implies(Or(A, B), A).generalize((A, B), conditions=(inBool(A), Not(B))).qed(__file__)
