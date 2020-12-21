from proveit import defaults, USE_DEFAULTS, ExprTuple
from proveit.logic import Membership, Nonmembership
from proveit.numbers import num
from proveit._common_ import a, b, c, m, n, x, y


class EnumMembership(Membership):
    '''
    Defines methods that apply to membership in an enumerated set.
    '''

    def __init__(self, element, domain):
        Membership.__init__(self, element)
        self.domain = domain

    def side_effects(self, judgment):
        '''
        Unfold the enumerated set membership, and in boolean as
        a side-effect.
        '''
        yield self.unfold

    def conclude(self, assumptions=USE_DEFAULTS):
        '''
        From [(element=x) or (element=y) or ..], derive and return
        [element in {x, y, ..}].
        '''
        from proveit import ProofFailure
        from ._theorems_ import fold_singleton, in_enumerated_set, fold
        enum_elements = self.domain.elements
        if len(enum_elements) == 1:
            return fold_singleton.instantiate(
                {x: self.element, y: enum_elements[0]}, assumptions=assumptions)
        else:
            try:
                idx = self.domain.operands.index(self.element)
                _a = self.domain.operands[:idx]
                _b = self.element
                _c = self.domain.operands[idx + 1:]
                _m = ExprTuple(*_a).length(assumptions=assumptions)
                _n = ExprTuple(*_c).length(assumptions=assumptions)
                return in_enumerated_set.instantiate(
                    {m: _m, n: _n, a: _a, b: _b, c: _c}, assumptions=assumptions)
            except (ProofFailure, ValueError) as e:
                return fold.instantiate({n: num(
                    len(enum_elements)), x: self.element, y: enum_elements}, assumptions=assumptions)

    def equivalence(self, assumptions=USE_DEFAULTS):
        '''
        From the EnumMembership object [element in {a, ..., n}],
        deduce and return:
        |– [element in {x, y, ..}] = [(element=a) or ... or (element=a)]
        '''
        from ._axioms_ import enum_set_def
        from ._theorems_ import singleton_def
        enum_elements = self.domain.elements

        if len(enum_elements) == 1:
            return singleton_def.instantiate(
                {x: self.element, y: enum_elements[0]}, assumptions=assumptions)
        else:
            return enum_set_def.instantiate({n: num(
                len(enum_elements)), x: self.element, y: enum_elements}, assumptions=assumptions)

    def derive_in_singleton(self, expression, assumptions=USE_DEFAULTS):
        # implemented by JML 6/28/19
        from proveit.logic import TRUE, FALSE
        from ._theorems_ import in_singleton_eval_false, in_singleton_eval_true
        if expression.rhs == FALSE:
            return in_singleton_eval_false.instantiate(
                {x: expression.lhs.element, y: expression.lhs.domain.elements[0]}, assumptions=assumptions)
        elif expression.rhs == TRUE:
            return in_singleton_eval_true.instantiate(
                {x: expression.lhs.element, y: expression.lhs.domain.elements[0]}, assumptions=assumptions)

    def unfold(self, assumptions=USE_DEFAULTS):
        '''
        From [element in {x, y, ..}], derive and return [(element=x) or (element=y) or ..].
        '''
        from ._theorems_ import unfold_singleton, unfold
        enum_elements = self.domain.elements
        if len(enum_elements) == 1:
            return unfold_singleton.instantiate(
                {x: self.element, y: enum_elements[0]}, assumptions=assumptions)
        else:
            return unfold.instantiate({n: num(
                len(enum_elements)), x: self.element, y: enum_elements}, assumptions=assumptions)

    def deduce_in_bool(self, assumptions=USE_DEFAULTS):
        from ._theorems_ import in_singleton_is_bool, in_enum_set_is_bool
        enum_elements = self.domain.elements
        if len(enum_elements) == 1:
            return in_singleton_is_bool.instantiate(
                {x: self.element, y: enum_elements[0]}, assumptions=assumptions)
        else:
            return in_enum_set_is_bool.instantiate(
                {n: num(len(enum_elements)), x: self.element, y: enum_elements},
                assumptions=assumptions)


class EnumNonmembership(Nonmembership):
    '''
    Defines methods that apply to non-membership in an enumerated set.
    '''

    def __init__(self, element, domain):
        Nonmembership.__init__(self, element)
        self.domain = domain

    def side_effects(self, judgment):
        '''
        Unfold the enumerated set nonmembership, and ....
        '''
        yield self.unfold

    def equivalence(self):
        '''
        Deduce and return
        |– [element not in {a, ..., n}] =
           [(element != a) and ... and (element != n)]
        where self is the EnumNonmembership object.
        '''
        from ._theorems_ import not_in_singleton_equiv, nonmembership_equiv
        enum_elements = self.domain.elements
        if len(enum_elements) == 1:
            return not_in_singleton_equiv.instantiate(
                {x: self.element, y: enum_elements})
        else:
            return nonmembership_equiv.instantiate(
                {n: num(len(enum_elements)), x: self.element,
                 y: enum_elements})

    def conclude(self, assumptions=USE_DEFAULTS):
        '''
        From [element != a] AND ... AND [element != n],
        derive and return [element not in {a, b, ..., n}],
        where self is the EnumNonmembership object.
        '''
        # among other things, convert any assumptions=None
        # to assumptions=()
        assumptions = defaults.checked_assumptions(assumptions)
        from ._theorems_ import nonmembership_fold
        enum_elements = self.domain.elements
        element = self.element
        operands = self.domain.operands
        return nonmembership_fold.instantiate(
            {n: num(len(enum_elements)), x: self.element, y: enum_elements},
            assumptions=assumptions)

    def unfold(self, assumptions=USE_DEFAULTS):
        '''
        From [element not-in {a, b, ..., n}], derive and return
        [(element!=a) AND (element!=b) AND ... AND (element!=n)].
        '''
        from ._theorems_ import (
            nonmembership_unfold, nonmembership_unfold_singleton)
        enum_elements = self.domain.elements
        if len(enum_elements) == 1:
            return nonmembership_unfold_singleton.instantiate(
                {x: self.element, y: enum_elements[0]},
                assumptions=assumptions)
        else:
            return nonmembership_unfold.instantiate(
                {n: num(len(enum_elements)), x: self.element, y: enum_elements},
                assumptions=assumptions)

    def deduce_in_bool(self, assumptions=USE_DEFAULTS):
        from ._theorems_ import not_in_singleton_is_bool, not_in_enum_set_is_bool
        enum_elements = self.domain.elements
        if len(enum_elements) == 1:
            return not_in_singleton_is_bool.instantiate(
                {x: self.element, y: enum_elements[0]}, assumptions=assumptions)
        else:
            # return nonmembership_equiv.instantiate(
            #     {n:num(len(enum_elements)), x:self.element, y:enum_elements})
            return not_in_enum_set_is_bool.instantiate(
                {n: num(len(enum_elements)), x: self.element, y: enum_elements})
