from proveit import defaults, Literal, Operation, ProofFailure, USE_DEFAULTS
from proveit import a, b, r, x, theta
from proveit.logic import InSet
from proveit.logic.sets import ProperSubset, SubsetEq
from proveit.numbers import Add, Mult


class Abs(Operation):
    # operator of the Abs operation.
    _operator_ = Literal(string_format='Abs', theory=__file__)

    def __init__(self, A):
        Operation.__init__(self, Abs._operator_, A)

    def string(self, **kwargs):
        return '|' + self.operand.string() + '|'

    def latex(self, **kwargs):
        return r'\left|' + self.operand.latex() + r'\right|'

    def not_equal(self, rhs, assumptions=USE_DEFAULTS):
        # accessed from conclude() method in not_equals.py
        from . import abs_not_eq_zero
        from proveit.logic import NotEquals
        from proveit.numbers import zero
        if rhs == zero:
            return abs_not_eq_zero.instantiate(
                {a: self.operand}, assumptions=assumptions)
        raise NotEquals(self, zero).conclude_as_folded(assumptions)

    def deduce_greater_than_equals_zero(self, assumptions=USE_DEFAULTS):
        from proveit.numbers import Complex
        from . import abs_is_non_neg
        return abs_is_non_neg.instantiate(
            {a: self.operand}, assumptions=assumptions)

    def distribute(self, assumptions=USE_DEFAULTS):
        '''
        Distribute the absolute value over a product or fraction.
        Assumptions may be needed to deduce that the sub-operands are
        complex numbers.
        This works fine for the Abs(Div()) case, but still
        eliciting an extract_init_arg_value error related to a multi-
        variable domain condition for the Mult case. See _demos_ pg
        for an example; WW thinks this is a prob with iterations and
        we'll fix/update this later.
        '''
        from . import abs_frac, abs_prod
        from proveit import n, x
        from proveit.numbers import Complex, Div, Mult
        if isinstance(self.operand, Div):
            return abs_frac.instantiate(
                {a: self.operand.numerator, b: self.operand.denominator},
                assumptions=assumptions)
        elif isinstance(self.operand, Mult):
            _x = self.operand.operands
            _n = _x.num_elements(assumptions)
            return abs_prod.instantiate(
                {n: _n, x: _x},
                assumptions=assumptions)
        else:
            raise ValueError(
                'Unsupported operand type for Abs.distribute() '
                'method: ', str(self.operand.__class__))

    def abs_elimination(self, operand_type=None, assumptions=USE_DEFAULTS):
        '''
        For some |x| expression, deduce either |x| = x (the default) OR
        |x| = -x (for operand_type = 'negative'). Assumptions may be
        needed to deduce x >= 0 or x < 0, respectively.
        '''

        from proveit.numbers import Neg
        from . import abs_non_neg_elim, abs_neg_elim
        # deduce_non_neg(self.operand, assumptions) # NOT YET IMPLEMENTED
        if operand_type is None or operand_type == 'non-negative':
            return abs_non_neg_elim.instantiate({x: self.operand},
                                                assumptions=assumptions)
        elif operand_type == 'negative':
            return abs_neg_elim.instantiate({x: self.operand},
                                            assumptions=assumptions)
        else:
            raise ValueError(
                "Unsupported operand type for Abs.abs_elimination() "
                "method; operand type should be omitted or specified "
                "as 'negative' or 'non-negative', but instead was "
                "given as operand_type = {}.".format(operand_type))

    def do_reduced_simplification(self, assumptions=USE_DEFAULTS):
        '''
        Returns a proven simplification equation for this absolute
        value expression if a simplification is known.
        
        Handles a number of absolute value simplifications:
            1. |x| = x given x in RealNonNeg 
                             (may try to prove this if easy to do)
            2. |x| = -x given x in RealNeg
                             (may try to prove this if easy to do)
            3. |r exp(i a)| = r given r in RealNonNeg, x in Real
            4. |r exp(i a) - r exp(i b)| = 2 r sin(|a - b|/2)
                given a and b in Real.
        '''
        from proveit.logic import Equals
        from proveit.numbers import greater, greater_eq, Neg
        from proveit.numbers import (zero, Natural, NaturalPos, 
                                     RealNeg, RealNonNeg, RealPos)
        # among other things, convert any assumptions=None
        # to assumptions=() (thus averting len(None) errors)
        assumptions = defaults.checked_assumptions(assumptions)

        #-- -------------------------------------------------------- --#
        #-- Case (1): Abs(x) where entire operand x is known or      --#
        #--           assumed to be non-negative Real.               --#
        #-- -------------------------------------------------------- --#
        if InSet(self.operand, RealNonNeg).proven(assumptions=assumptions):
            # Entire operand is known to be or assumed to be a
            # non-negative real, so we can return Abs(x) = x
            return self.abs_elimination(operand_type='non-negative',
                                        assumptions=assumptions)

        #-- -------------------------------------------------------- --#
        #-- Case (2): Abs(x) where entire operand x is known or      --#
        #--           assumed to be a negative Real.                 --#
        #-- -------------------------------------------------------- --#
        if InSet(self.operand, RealNeg).proven(assumptions=assumptions):
            # Entire operand is known to be or assumed to be a
            # negative real, so we can return Abs(x) = -x
            return self.abs_elimination(operand_type='negative',
                                        assumptions=assumptions)

        #-- -------------------------------------------------------- --#
        # -- Case (3): Abs(x) where entire operand x is not yet known --*
        #--           to be a non-negative Real, but can easily be   --#
        #--           proven to be a non-negative Real because it is --#
        # --           (a) known or assumed to be ≥ 0 or
        #--           (b) known or assumed to be in a subset of the  --#
        #--               non-negative Real numbers, or              --#
        #--           (c) the addition or product of operands, all   --#
        #--               of which are known or assumed to be non-   --#
        # --               negative real numbers. TBA!
        #-- -------------------------------------------------------- --#
        if (greater(self.operand, zero).proven(assumptions=assumptions) and
                not greater_eq(self.operand, zero).proven(assumptions=assumptions)):
            greater_eq(self.operand, zero).prove(assumptions=assumptions)
            # and then it will get picked up in the next if() below

        if greater_eq(self.operand, zero).proven(assumptions=assumptions):
            from proveit.numbers.number_sets.real_numbers import (
                in_real_non_neg_if_greater_eq_zero)
            in_real_non_neg_if_greater_eq_zero.instantiate(
                {a: self.operand}, assumptions=assumptions)
            return self.abs_elimination(operand_type='non-negative',
                                        assumptions=assumptions)

        if self.operand in InSet.known_memberships.keys():
            for kt in InSet.known_memberships[self.operand]:
                if kt.is_sufficient(assumptions):
                    if is_equal_to_or_subset_eq_of(
                            kt.expr.operands[1],
                            equal_sets=[RealNonNeg, RealPos],
                            subset_eq_sets=[Natural, NaturalPos, RealPos],
                            assumptions=assumptions):

                        InSet(self.operand, RealNonNeg).prove(
                            assumptions=assumptions)
                        return self.abs_elimination(
                            operand_type='non-negative', assumptions=assumptions)

        if isinstance(self.operand, Add) or isinstance(self.operand, Mult):
            count_of_known_memberships = 0
            count_of_known_relevant_memberships = 0
            for op in self.operand.operands:
                if op in InSet.known_memberships.keys():
                    count_of_known_memberships += 1
            if (count_of_known_memberships == 
                    self.operand.operands.num_entries()):
                for op in self.operand.operands:
                    op_temp_known_memberships = InSet.known_memberships[op]
                    for kt in op_temp_known_memberships:
                        if (kt.is_sufficient(assumptions)
                            and is_equal_to_or_subset_eq_of(
                            kt.expr.operands[1],
                            equal_sets=[RealNonNeg, RealPos],
                            subset_eq_sets=[Natural, NaturalPos,
                                            RealPos, RealNonNeg],
                                assumptions=assumptions)):

                            count_of_known_relevant_memberships += 1
                            break

                if (count_of_known_relevant_memberships ==
                        self.operand.operands.num_entries()):
                    # Prove that the sum or product is in
                    # RealNonNeg and then instantiate abs_elimination.
                    for op in self.operand.operands:
                        InSet(op, RealNonNeg).prove(assumptions=assumptions)
                    return self.abs_elimination(assumptions=assumptions)

        #-- -------------------------------------------------------- --#
        #-- Case (4): Abs(x) where operand x can easily be proven    --#
        #--           to be a negative Real number because -x is     --#
        #--           known to be in a subset of the positive Real   --#
        #--           numbers.                                       --#
        #-- -------------------------------------------------------- --#
        negated_op = None
        if isinstance(self.operand, Neg):
            negated_op = self.operand.operand
        else:
            negated_op = Neg(self.operand)
        negated_op_simp = negated_op.simplification(
            assumptions=assumptions).rhs

        if negated_op_simp in InSet.known_memberships.keys():
            from proveit.numbers.number_sets.real_numbers import (
                neg_is_real_neg_if_pos_is_real_pos)
            for kt in InSet.known_memberships[negated_op_simp]:
                if kt.is_sufficient(assumptions):
                    if is_equal_to_or_subset_eq_of(
                            kt.expr.operands[1],
                            equal_sets=[RealNonNeg, RealPos],
                            subset_sets=[NaturalPos, RealPos],
                            subset_eq_sets=[NaturalPos, RealPos],
                            assumptions=assumptions):

                        InSet(negated_op_simp, RealPos).prove(
                            assumptions=assumptions)
                        neg_is_real_neg_if_pos_is_real_pos.instantiate(
                            {a: negated_op_simp}, assumptions=assumptions)
                        return self.abs_elimination(operand_type='negative',
                                                    assumptions=assumptions)
        
        #-- -------------------------------------------------------- --#
        #-- Case (5):   |r exp(i a)| = r   or   |x exp(i a)| = |x|   --#
        #-- -------------------------------------------------------- --#
        try:
            # Grab polar coordinates without automation so we don't
            # waste time if it isn't in a complex polar form (or 
            # obviously equivalent to this form).
            return self.complex_magnitude_simplification(
                    assumptions=assumptions, automation=False)
        except ValueError:
            # Not in a complex polar form.
            pass

        #-- -------------------------------------------------------- --#
        #-- Case (6): |r exp(i a) - r exp(i b)| = 2 r sin(|a - b|/2) --#
        #-- -------------------------------------------------------- --#
        if (isinstance(self.operand, Add) and 
                self.operand.operands.is_double()):
            try:
                # Grab polar coordinates without automation so we don't
                # waste time if it isn't in a complex polar form (or 
                # obviously equivalent to this form).
                return self.complex_circle_coord_length_simplification(
                        assumptions=assumptions, automation=False)
            except ValueError:
                # Not in a complex polar form.
                pass

        # Default is no simplification.
        return Equals(self, self).prove(assumptions)
    
    def deduce_in_number_set(self, number_set, assumptions=USE_DEFAULTS):
        '''
        Given a number set number_set (such as Integer, Real, etc),
        attempt to prove that the given expression is in that number
        set using the appropriate closure theorem.
        '''
        from proveit.numbers.absolute_value import (
            abs_rational_closure, abs_rational_non_zero_closure,
            abs_complex_closure, abs_nonzero_closure,
            abs_complex_closure_non_neg_real)
        from proveit.numbers import (
            Rational, RationalNonZero, RationalPos, RationalNeg,
            RationalNonNeg, Real, RealNonNeg, RealPos)

        # among other things, make sure non-existent assumptions
        # manifest as empty tuple () rather than None
        assumptions = defaults.checked_assumptions(assumptions)

        thm = None
        if number_set in (RationalPos, RationalNonZero):
            thm = abs_rational_non_zero_closure
        elif number_set in (Rational, RationalNonNeg, RationalNeg):
            thm = abs_rational_closure
        elif number_set == Real:
            thm = abs_complex_closure
        elif number_set == RealPos:
            thm = abs_nonzero_closure
        elif number_set == RealNonNeg:
            thm = abs_complex_closure_non_neg_real

        if thm is not None:
            in_set = thm.instantiate({a: self.operand},
                                     assumptions=assumptions)
            if in_set.domain == number_set:
                # Exactly the domain we were looking for.
                return in_set
            # We must have proven we were in a subset of the
            # one we were looking for.
            return InSet(self, number_set).prove(assumptions)

        # To be thorough and a little more general, we check if the
        # specified number_set is already proven to *contain* one of
        # the number sets we have theorems for -- for example,
        #     Y=Complex contain X=Real, and
        #     Y=(-1, inf) contains X=RealPos,
        # but we don't have specific thms for those supersets Y.
        # If so, use the appropiate thm to determine that self is in X,
        # then prove that self must also be in Y since Y contains X.
        if SubsetEq(Real, number_set).proven(assumptions=assumptions):
            abs_complex_closure.instantiate({a: self.operand},
                                            assumptions=assumptions)
            return InSet(self, number_set).prove(assumptions=assumptions)
        if SubsetEq(RealPos, number_set).proven(assumptions=assumptions):
            abs_nonzero_closure.instantiate({a: self.operand},
                                            assumptions=assumptions)
            return InSet(self, number_set).prove(assumptions=assumptions)
        if SubsetEq(RealNonNeg, number_set).proven(assumptions=assumptions):
            abs_complex_closure_non_neg_real.instantiate(
                {a: self.operand}, assumptions=assumptions)
            return InSet(self, number_set).prove(assumptions=assumptions)

        # otherwise, we just don't have the right thm to make it work
        msg = ("'Abs.deduce_in_number_set()' not implemented for "
               "the %s set" % str(number_set))
        raise ProofFailure(InSet(self, number_set), assumptions, msg)

    def complex_magnitude_simplification(self, assumptions=USE_DEFAULTS,
                                         automation=True):
        from proveit.numbers import (one, RealNonNeg,
                                     complex_polar_coordinates)
        from proveit.trigonometry import (complex_unit_circle_mag,
                                          complex_polar_mag,
                                          complex_polar_mag_using_abs)
        reductions = set()
        _r, _theta = complex_polar_coordinates(
                self.operand, assumptions=assumptions,
                automation=automation, simplify=True, 
                radius_must_be_nonneg=False, nonneg_radius_preferred=True, 
                reductions=reductions)
        if _r == one:
            # |exp(i*theta)| = 1
            return complex_unit_circle_mag.instantiate(
                    {theta:_theta}, reductions=reductions,
                    assumptions=assumptions)
        elif InSet(_r, RealNonNeg).proven(assumptions):
            # |r exp(i*theta)| = r
            return complex_polar_mag.instantiate(
                    {r: _r, theta: _theta}, reductions=reductions,
                    assumptions=assumptions)
        else:
            # |r exp(i*theta)| = |r|, is the best we can do.
            return complex_polar_mag_using_abs.instantiate(
                    {r: _r, theta: _theta}, reductions=reductions,
                    assumptions=assumptions)

    def complex_circle_coord_length_simplification(
            self, assumptions=USE_DEFAULTS, automation=True):
        from proveit.numbers import (one, Neg, subtract, 
                                     complex_polar_coordinates)
        from proveit.trigonometry import (complex_unit_circle_chord_length,
                                          complex_circle_chord_length)
        def raise_not_valid_form():
            raise ValueError(
                    "Complex circle coord length is only applicable to "
                    "expressions of the form |r exp(i a) - r exp(i b)| "
                    "or obviously equivalent. "
                    "%s does not qualify."%self)
            
        if not (isinstance(self.operand, Add) and 
                self.operand.operands.is_double()):
            raise_not_valid_form()
        
        reductions = set()
        # Grab polar coordinates without automation so we don't
        # waste time if it isn't in a complex polar form (or 
        # obviously equivalent to this form).
        term1 = self.operand.terms[0]
        term2 = self.operand.terms[1]
        if isinstance(term2, Neg):
            term2 = term2.operand
        else:
            term2 = Neg(term2)
        _r1, _theta1 = complex_polar_coordinates(
                term1, assumptions=assumptions,
                automation=automation, simplify=True, reductions=reductions)
        _r2, _theta2 = complex_polar_coordinates(
                term2, assumptions=assumptions,
                automation=automation, simplify=True, reductions=reductions)
        if _r1 == _r2:
            # Only applicable if the magnitudes are the same.
            reductions.add(Abs(subtract(_theta1, _theta2)).simplification(
                    assumptions=assumptions))
            if _r1 == one:
                return complex_unit_circle_chord_length.instantiate(
                        {a:_theta1, b:_theta2}, 
                        reductions=reductions, assumptions=assumptions)
            else:
                return complex_circle_chord_length.instantiate(
                        {r: _r1, a:_theta1, b:_theta2}, 
                        reductions=reductions, assumptions=assumptions)
        raise_not_valid_form()

def is_equal_to_or_subset_eq_of(
        number_set, equal_sets=None, subset_sets=None, subset_eq_sets=None,
        assumptions=None):
    '''
    A utility function used in the do_reduced_simplification() method
    to test whether the number set specified by number_set:
    • is equal to any of the number sets provided in the list of
      equal_sets
    • OR is already known/proven to be a proper subset of any of the
      number sets provided in the list of subset_sets,
    • OR is already known/proven to be an improper subset of any of the
      number sets provided in the list of subset_eq_sets,
    returning True at the first such equality, subset, or subset_eq
    relation found to be True.
    '''
    # among other things, convert any assumptions=None
    # to assumptions=() (thus averting len(None) errors)
    assumptions = defaults.checked_assumptions(assumptions)

    if equal_sets is not None:
        for temp_set in equal_sets:
            if number_set == temp_set:
                return True
    if subset_eq_sets is not None:
        for temp_set in subset_eq_sets:
            if SubsetEq(number_set, temp_set).proven(assumptions):
                return True
    if subset_sets is not None:
        for temp_set in subset_sets:
            if ProperSubset(number_set, temp_set).proven(assumptions):
                return True
    return False
