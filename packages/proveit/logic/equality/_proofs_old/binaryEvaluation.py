from proveit.basiclogic.equality.theorems import binary_substitution
from proveit.basiclogic import Implies, And, Equals
from proveit.common import a, b, c, f, x, y, fab

# hypothesis = (x=a and y=b)
hypothesis = And(Equals(x, a), Equals(y, b))
# [f(x, y) = f(a, b)] assuming hypothesis
fxy_eq_fab = binary_substitution.instantiate().derive_conclusion().proven({hypothesis})
# [f(a, b)=c] => [f(x, y)=c] assuming hypothesis
conclusion = fxy_eq_fab.transitivity_impl(Equals(fab, c)).proven({hypothesis})
# forall_{f, x, y, a, b, c} [x=a and y=b] => {[f(a, b)=c] => [f(x, y)=c]}
Implies(hypothesis, conclusion).generalize((f, x, y, a, b, c)).qed(__file__)
