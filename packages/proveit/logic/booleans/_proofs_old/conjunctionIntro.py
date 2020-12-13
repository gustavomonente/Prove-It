from proveit.basiclogic.booleans.theorems import trueAndTrue
from proveit.basiclogic import deriveStmtEqTrue, And, TRUE
from proveit.common import A, B, X

# A=TRUE assuming A
AeqT = deriveStmtEqTrue(A).proven({A})
# B=TRUE assuming B
BeqT = deriveStmtEqTrue(B).proven({B})
# TRUE AND TRUE
trueAndTrue
# (TRUE and B) assuming B via (TRUE and TRUE)
BeqT.subLeftSideInto(And(TRUE, X), X).proven({B})
# (A and B) assuming A, B via (TRUE and TRUE)
AeqT.subLeftSideInto(And(X, B), X).proven({A, B})
# forall_{A | A, B | B} (A and B)
And(A, B).generalize((A, B), conditions=(A, B)).qed(__file__)
