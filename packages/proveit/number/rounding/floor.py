from proveit import defaults, Function, InnerExpr, Literal, USE_DEFAULTS
from proveit.number.sets import Integers, Naturals
from proveit.number.rounding.rounding_methods import (
    apply_roundingElimination, apply_roundingExtraction)

class Floor(Function):
    # operator of the Floor operation.
    _operator_ = Literal(stringFormat='floor', context=__file__)
    
    def __init__(self, A):
        Function.__init__(self, Floor._operator_, A)
        # self.operand = A # check later that the operand attribute
        # is still working!
            
    def latex(self, **kwargs):
        return r'\lfloor ' + self.operand.latex(fence=False) + r'\rfloor'

    def doReducedSimplification(self, assumptions=USE_DEFAULTS):
        '''
        Created: 3/30/2020 by wdc.
        Last modified: 3/30/2020 by wdc. Creation. Based on roughly
                       analogous methods in Add and Exp classes. May
                       need to be renamed.

        For the trivial case where the operand is an integer,
        derive and return this Floor expression equated with the
        operand itself. Assumptions may be necessary to deduce
        necessary conditions for the simplification.
        For the case where the operand is of the form (real + int),
        derive and return this Floor expression equated with
        Round(real) + int.
        CONSIDER ADDING A RECURSIVE COMPONENT to allow further 
        simplfication, for example for Floor(real + int + int).
        '''
        from proveit._common_ import n, x
        from proveit.number import Add, Integers
        from ._theorems_ import floorOfInteger, floorOfRealPlusInt
        try:
            return floorOfInteger.specialize(
                    {x:self.operand}, assumptions=assumptions)
        except:
            if isinstance(self.operand, Add):
                subops = self.operand.operands
                if len(subops)==2:
                    xsub = subops[0]
                    nsub = subops[1]
                else:
                    xsub = Add(subops[:-1])
                    n: subops[-1]
                return floorOfRealPlusInt.specialize(
                        {x:xsub, n:nsub}, assumptions=assumptions)
            else:
                raise ValueError("Floor.doReducedSimplification() method "
                                 "expecting simpler operands. Consider "
                                 "reviewing the floorOfInteger and "
                                 "floorOfRealPlusInt theorems in the "
                                 "proveit/number/rounding context.")

    def roundingElimination(self, assumptions=USE_DEFAULTS):
        '''
        For the trivial case of Floor(x) where the operand x is already
        an integer, derive and return this Floor expression equated
        with the operand itself: Floor(x) = x. Assumptions may be
        necessary to deduce necessary conditions (for example, that x
        actually is an integer) for the simplification.
        This method is utilized by the doReducedSimplification() method
        only after the operand x is verified to already be proven
        (or assumed) to be an integer.
        For the case where the operand is of the form x = real + int,
        see the roundingExtraction() method.
        '''
        from ._theorems_ import floorOfInteger

        return apply_roundingElimination(self, floorOfInteger, assumptions)

    def roundingExtraction(self, idx_to_extract=None, assumptions=USE_DEFAULTS):
        '''
        For the case of Floor(x) where the operand x = x_real + x_int,
        derive and return Floor(x) = Floor(x_real) + int (thus
        'extracting' the integer component out from the Floor() fxn).
        The idx_to_extract is the zero-based index of the item in the
        operands of an Add(a, b, …, n) expression to attempt to extract.
        Assumptions may be necessary to deduce necessary conditions
        (for example, that x_int actually is an integer) for the
        simplification.
        This method is utilized by the doReducedSimplification() method
        only after the operand x is verified to already be proven
        (or assumed) to be of the form x = x_real + x_int.
        For the case where the entire operand x is itself an integer,
        see the roundingElimination() method.

        This works only if the operand x is an instance of the Add
        class at its outermost level, e.g. x = Add(a, b, …, n). The
        operands of that Add class can be other things, but the
        extraction is guaranteed to work only if the inner operands
        a, b, etc., are simple.
        '''
        from ._theorems_ import floorOfRealPlusInt
        return apply_roundingExtraction(
            self, floorOfRealPlusInt, idx_to_extract, assumptions)
        
    def deduceInNumberSet(self, number_set, assumptions=USE_DEFAULTS):
        '''
        Given a number set number_set, attempt to prove that the given
        Floor expression is in that number set using the appropriate
        closure theorem.
        '''
        from proveit._common_ import x
        from proveit.logic import InSet
        from proveit.number.rounding._theorems_ import (
                  floorRealClosure, floorRealPosClosure)

        # among other things, convert any assumptions=None
        # to assumptions=()
        assumptions = defaults.checkedAssumptions(assumptions)

        if number_set == Integers:
            return floorRealClosure.specialize({x:self.operand},
                      assumptions=assumptions)

        if number_set == Naturals:
            return floorRealPosClosure.specialize({x:self.operand},
                      assumptions=assumptions)

        msg = ("'Floor.deduceInNumberSet()' not implemented for the "
               "%s set"%str(number_set))
        raise ProofFailure(InSet(self, number_set), assumptions, msg)

# Register these generic expression equivalence methods:
InnerExpr.register_equivalence_method(
        Floor, 'roundingElimination', 'roundingEliminated', 'roundingEliminate')
InnerExpr.register_equivalence_method(
        Floor, 'roundingExtraction', 'roundingExtracted', 'roundingExtract')
