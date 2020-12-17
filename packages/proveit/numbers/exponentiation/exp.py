from proveit import (Literal, Operation, ExprTuple, InnerExpr, ProofFailure,
                     maybeFencedString, USE_DEFAULTS, StyleOptions)
from proveit.logic import Membership
import proveit._common_
from proveit._common_ import a, b, c, k, m, n, x, S
from proveit.numbers import one, two, Div, frac, num

class Exp(Operation):
    # operator of the Exp operation.
    _operator_ = Literal(stringFormat='Exp', theory=__file__)    
    
    def __init__(self, base, exponent):
        r'''
        Raise base to exponent power.
        '''
        Operation.__init__(self, Exp._operator_, (base, exponent),
                           styles={'exponent':'raised'})
        self.base = base
        self.exponent = exponent

    def remakeConstructor(self):
        if self.getStyle('exponent') == 'radical':
            # Use a different constructor if using the 'radical' style.
            if self.exponent == frac(one, two):
                return 'sqrt' 
            else:
                raise ValueError("Unkown radical type, exponentiating to the power "
                                 "of %s"%str(self.exponent))
        return Operation.remakeConstructor(self)
    
    def remakeArguments(self):
        '''
        Yield the argument values or (name, value) pairs
        that could be used to recreate the Operation.
        '''
        if self.getStyle('exponent') == 'radical':
            yield self.base
        else:
            yield self.base
            yield self.exponent
    
    def membershipObject(self, element):
        return ExpSetMembership(element, self)
    
    def _closureTheorem(self, numberSet):
        import natural.theorems
        import real.theorems
        import complex.theorems
        from proveit.numbers import two
        if numberSet == NaturalPos:
            return natural.theorems.powClosure
        elif numberSet == Real:
            return real.theorems.powClosure
        elif numberSet == RealPos:
            if self.exponent != two: # otherwise, use
                                     # deduceInRealPosDirectly(..)
                return real.theorems.powPosClosure            
        elif numberSet == Complex:
            return complex.theorems.powClosure
    
    def doReducedSimplification(self, assumptions=USE_DEFAULTS):
        '''
        For trivial cases, a zero or one exponent or zero or one base,
        derive and return this exponential expression equated with a
        simplified form. Assumptions may be necessary to deduce
        necessary conditions for the simplification.
        '''
        from proveit.logic import Equals, InSet
        from proveit.numbers import one, two, Rational, Real, Abs
        from proveit.relation import TransRelUpdater
        from ._theorems_ import complexXToFirstPowerIsX
        if self.exponent == one:
            return complexXToFirstPowerIsX.instantiate({a:self.base})
        if (isinstance(self.base, Exp) and
            isinstance(self.base.exponent, Div) and
            self.base.exponent.numerator==one and
            self.base.exponent.denominator == self.exponent):
            from ._theorems_ import nth_power_of_nth_root
            _n, _x = nth_power_of_nth_root.instanceParams
            return nth_power_of_nth_root.instantiate(
                {_n:self.exponent, _x:self.base.base}, assumptions=assumptions)
        
        expr = self
        # for convenience updating our equation:
        eq = TransRelUpdater(expr, assumptions) 
        if self.exponent == two and isinstance(self.base, Abs):
            from ._theorems_ import (square_abs_rational_simp, 
                                     square_abs_real_simp)
            # |a|^2 = a if a is real
            rational_base = InSet(self.base, Rational).proven(assumptions)
            real_base = InSet(self.base, Real).proven(assumptions)
            thm = None
            if rational_base:
                thm = square_abs_rational_simp
            elif real_base:
                thm = square_abs_real_simp
            if thm is not None:
                simp = thm.instantiate({a:self.base.operand}, 
                                       assumptions=assumptions)
                expr = eq.update(simp)
                # A further simplification may be possible after
                # eliminating the absolute value.
                expr = eq.update(expr.simplification(assumptions))

        return eq.relation

    def doReducedEvaluation(self, assumptions=USE_DEFAULTS):
        '''
        For trivial cases, a zero or one exponent or zero or one base,
        derive and return this exponential expression equated with a
        evaluated form. Assumptions may be necessary to deduce
        necessary conditions for the simplification.
        '''
        from proveit.logic import EvaluationError
        from proveit.numbers import zero, one
        from ._theorems_ import expZeroEqOne, exponentiatedZero, exponentiatedOne
        if self.exponent == zero:
            return expZeroEqOne.instantiate({a:self.base}) # =1
        elif self.base == zero:
            return exponentiatedZero.instantiate({x:self.exponent}) # =0
        elif self.base == one:
            return exponentiatedOne.instantiate({x:self.exponent}) # =1
        else:
            raise EvaluationError('Only trivial evaluation is implemented '
                                  '(zero or one for the base or exponent).',
                                  assumptions)
    
    def deduce_not_zero(self, assumptions=USE_DEFAULTS):
        '''
        Prove that this exponential is not zero given that
        the base is not zero.
        '''
        from proveit.logic import InSet
        from proveit.numbers import RationalPos
        from ._theorems_ import exp_rational_non_zero__not_zero, expNotEqZero
        if (not expNotEqZero.isUsable() or (
                InSet(self.base, RationalPos).proven(assumptions) and
                InSet(self.exponent, RationalPos).proven(assumptions))):
            # Special case where the base and exponent are RationalPos.
            return exp_rational_non_zero__not_zero.instantiate(
                    {a:self.base, b:self.exponent}, assumptions=assumptions)
        return expNotEqZero.instantiate(
                {a:self.base, b:self.exponent}, assumptions=assumptions)
    
    def deduceInRealPosDirectly(self, assumptions=frozenset()):
        import real.theorems
        from number import two
        if self.exponent == two:
            deduceInReal(self.base, assumptions)
            deduceNotZero(self.base, assumptions)
            return real.theorems.sqrdClosure.instantiate(
                {a:self.base}).checked(assumptions)
        # only treating certain special case(s) in this manner
        raise DeduceInNumberSetException(self, RealPos, assumptions)

    def expansion(self, assumptions=USE_DEFAULTS):
        '''
        From self of the form x^n return x^n = x(x)...(x).
        For example, Exp(x, two).expansion(assumptions)
        should return: assumptions |- (x^2) =  (x)(x). Currently only
        implemented explicitly for powers of n=2 and n=3.
        '''
        exponent = self.exponent
        if exponent == num(2):
            from ._theorems_ import square_expansion
            _x = square_expansion.instanceParam
            return square_expansion.instantiate(
                    {_x:self.base}, assumptions=assumptions)

        if exponent == 3:
            from ._theorems_ import  cube_expansion
            _x = cube_expansion.instanceParam
            return cube_expansion.instantiate(
                    {_x:self.base}, assumptions=assumptions)

        raise ValueError("Exp.expansion() implemented only for exponential "
                         "powers n=2 or n=3, but received an exponential "
                         "power of {0}.".format(exponent))

    def _notEqZeroTheorem(self):
        import complex.theorems
        return complex.theorems.powNotEqZero

    def styleOptions(self):
        options = StyleOptions(self)
        options.add('exponent',
                    "'raised': exponent as a superscript; "
                    "'radical': using a radical sign")
        return options
    

    def string(self, **kwargs):
        return self.formatted('string', **kwargs)

    def latex(self, **kwargs):
        return self.formatted('latex', **kwargs)
            
    def formatted(self, formatType, **kwargs):
        # begin building the inner_str
        inner_str = self.base.formatted(formatType, fence=True, forceFence=True)
        if self.getStyle('exponent') == 'raised':
            inner_str = (
                    inner_str
                    + r'^{'+self.exponent.formatted(formatType, fence=False)
                    + '}')
        elif self.getStyle('exponent') == 'radical':
            if self.exponent == frac(one, two):
                if formatType == 'string':
                    inner_str = (
                            r'sqrt('
                            + self.base.formatted(formatType, fence=True,
                                                  forceFence=True)
                            + ')')
                elif formatType == 'latex':
                    inner_str = (
                            r'\sqrt{'
                            + self.base.formatted(formatType, fence=True,
                                                  forceFence=True)
                            + '}')
            else:
                raise ValueError("Unkown radical type, exponentiating to the power "
                                 "of %s"%str(self.exponent))
                
        # only fence if forceFence=True (nested exponents is an
        # example of when fencing must be forced)
        kwargs['fence'] = (
            kwargs['forceFence'] if 'forceFence' in kwargs else False)
        return maybeFencedString(inner_str, **kwargs)
    
    def distribution(self, assumptions=USE_DEFAULTS):
        '''
        Equate this exponential to a form in which the exponent
        is distributed over factors, or a power of a power reduces to
        a power of multiplied exponents.
        Examples:
            (a*b*c)^f = a^f * b^f * c^f
            (a/b)^f = (a^f / b^f) 
            (a^b)^c = a^(b*c)
        '''
        from proveit.logic import InSet
        from proveit.numbers import Mult, Div, NaturalPos, RealPos, Real
        from ._theorems_ import (
                posnat_power_of_product, posnat_power_of_products,
                posnat_power_of_quotient, posnat_power_of_posnat_power,
                pos_power_of_product, pos_power_of_products, 
                pos_power_of_quotient, pos_power_of_pos_power,
                real_power_of_product, real_power_of_products,
                real_power_of_quotient, real_power_of_real_power,
                complex_power_of_product, complex_power_of_products, 
                complex_power_of_quotient, complex_power_of_complex_power)
        base = self.base
        exponent = self.exponent
        if isinstance(base, Mult):
            if self.base.operands.is_binary():
                _a, _b = self.base.operands
            else:
                _m = self.operands.length(assumptions)
                _a = self.operands
            if InSet(exponent, NaturalPos).proven(assumptions):
                if self.base.operands.is_binary():
                    return posnat_power_of_product.instantiate(
                            {a:_a, b:_b, n:exponent}, assumptions=assumptions)
                else:
                    return posnat_power_of_products.instantiate(
                            {m:_m, a:_a, n:exponent}, assumptions=assumptions)
            elif InSet(exponent, RealPos).proven(assumptions):
                if self.base.operands.is_binary():
                    return pos_power_of_product.instantiate(
                            {a:_a, b:_b, c:exponent}, assumptions=assumptions)
                else:
                    return pos_power_of_products.instantiate(
                            {m:_m, a:_a, c:exponent}, assumptions=assumptions)
            elif InSet(exponent, Real).proven(assumptions):
                if self.base.operands.is_binary():
                    return real_power_of_product.instantiate(
                            {a:_a, b:_b, c:exponent}, assumptions=assumptions)
                else:
                    return real_power_of_products.instantiate(
                            {m:_m, a:_a, c:exponent}, assumptions=assumptions)
            else: # Complex is the default
                if self.base.operands.is_binary():
                    return complex_power_of_product.instantiate(
                            {a:_a, b:_b, c:exponent}, assumptions=assumptions)
                else:
                    return complex_power_of_products.instantiate(
                            {m:_m, a:_a, c:exponent}, assumptions=assumptions)                      
        elif isinstance(base, Div):
            assert self.base.operands.is_binary()
            _a, _b = self.base.operands
            if InSet(exponent, NaturalPos).proven(assumptions):
                return posnat_power_of_quotient.instantiate(
                        {a:_a, b:_b, n:exponent}, assumptions=assumptions)
            else:
                if InSet(exponent, RealPos).proven(assumptions):
                    thm = pos_power_of_quotient
                elif InSet(exponent, Real).proven(assumptions):
                    thm = real_power_of_quotient
                else: # Complex is the default
                    thm = complex_power_of_quotient
                return thm.instantiate(
                        {a:_a, b:_b, c:exponent}, assumptions=assumptions)
        elif isinstance(base, Exp):
            _a = base.base
            if InSet(exponent, NaturalPos).proven(assumptions):
                _m, _n = base.exponent, exponent
                return posnat_power_of_posnat_power.instantiate(
                        {a:_a, m:_m, n:_n}, assumptions=assumptions)
            else:
                _b, _c = base.exponent, exponent
                if InSet(exponent, RealPos).proven(assumptions):
                    thm = pos_power_of_pos_power
                elif InSet(exponent, Real).proven(assumptions):
                    thm = real_power_of_real_power
                else: # Complex is the default
                    thm = complex_power_of_complex_power 
                return thm.instantiate(
                            {a:_a, b:_b, c:_c}, assumptions=assumptions)
        else:
            raise ValueError("May only distribute an exponent over a "
                             "product or fraction.")
        
    """
    def distributeExponent(self, assumptions=frozenset()):
        from proveit.numbers import Div
        from proveit.numbers.division.theorems import (
                fracIntExpRev, fracNatPosExpRev)
        if isinstance(self.base, Div):
            exponent = self.exponent
            try:
                deduceInNaturalPos(exponent, assumptions)
                deduceInComplex([self.base.numerator, self.base.denominator],
                                  assumptions)
                deduceNotZero(self.base.denominator, assumptions)
                return fracNatPosExpRev.instantiate(
                        {n:exponent}).instantiate(
                            {a:self.numerator.base, b:self.denominator.base})
            except:
                deduceInInteger(exponent, assumptions)
                deduceInComplex([self.base.numerator, self.base.denominator],
                                  assumptions)
                deduceNotZero(self.base.numerator, assumptions)
                deduceNotZero(self.base.denominator, assumptions)
                return fracIntExpRev.instantiate(
                        {n:exponent}).instantiate(
                            {a:self.base.numerator, b:self.base.denominator})
        raise Exception('distributeExponent currently only implemented for a '
                        'fraction base')
    """
        
    def raiseExpFactor(self, expFactor, assumptions=USE_DEFAULTS):
        # Note: this is out-of-date.  Distribution handles this now,
        # except it doesn't deal with the negation part
        # (do we need it to?)
        from proveit.numbers import Neg
        from .theorems import intExpOfExp, intExpOfNegExp
        if isinstance(self.exponent, Neg):
            b_times_c = self.exponent.operand
            thm = intExpOfNegExp
        else:
            b_times_c = self.exponent
            thm = intExpOfExp
        if not hasattr(b_times_c, 'factor'):
            raise ValueError('Exponent not factorable, may not raise the '
                             'exponent factor.')
        factorEq = b_times_c.factor(expFactor, pull='right',
                                    groupRemainder=True,
                                    assumptions=assumptions)
        if factorEq.lhs != factorEq.rhs:
            # factor the exponent first, then raise this exponent factor
            factoredExpEq = factorEq.substitution(self)
            return factoredExpEq.applyTransitivity(
                    factoredExpEq.rhs.raiseExpFactor(expFactor,
                                                     assumptions=assumptions))
        nSub = b_times_c.operands[1]
        aSub = self.base
        bSub = b_times_c.operands[0]
        deduceNotZero(aSub, assumptions)
        deduceInInteger(nSub, assumptions)
        deduceInComplex([aSub, bSub], assumptions)
        return thm.instantiate({n:nSub}).instantiate({a:aSub, b:bSub}).deriveReversed()

    def lowerOuterExp(self, assumptions=frozenset()):
        # 
        from proveit.numbers import Neg
        from .theorems import (
                intExpOfExp, intExpOfNegExp, negIntExpOfExp, negIntExpOfNegExp)
        if not isinstance(self.base, Exp):
            raise Exception('May only apply lowerOuterExp to nested '
                            'Exp operations')
        if isinstance(self.base.exponent, Neg) and isinstance(self.exponent, Neg):
            b_, n_ = self.base.exponent.operand, self.exponent.operand
            thm = negIntExpOfNegExp
        elif isinstance(self.base.exponent, Neg):
            b_, n_ = self.base.exponent.operand, self.exponent
            thm = intExpOfNegExp
        elif isinstance(self.exponent, Neg):
            b_, n_ = self.base.exponent, self.exponent.operand
            thm = negIntExpOfExp
        else:
            b_, n_ = self.base.exponent, self.exponent
            thm = intExpOfExp
        a_ = self.base.base
        deduceNotZero(self.base.base, assumptions)
        deduceInInteger(n_, assumptions)
        deduceInComplex([a_, b_], assumptions)
        return thm.instantiate({n:n_}).instantiate({a:a_, b:b_})

    def deduceInNumberSet(self, number_set, assumptions=USE_DEFAULTS):
        '''
        Given a number set number_set, attempt to prove that the given
        expression is in that number set using the appropriate closure
        theorem. This method uses instantiated thms for the sqrt() cases.
        Created: 2/20/2020 by wdc, based on the same method in the Add
                 class.
        Last modified: 2/28/2020 by wdc. Added instantiation for
                       sqrt() cases created using the sqrt() fxn.
        Last Modified: 2/20/2020 by wdc. Creation.
        Once established, these authorship notations can be deleted.
        '''
        from proveit.logic import InSet
        from proveit.numbers.exponentiation._theorems_ import (
                  expComplexClosure, expNatClosure, expRealClosure,
                  expRealClosureExpNonZero,expRealClosureBasePos,
                  expRealPosClosure, sqrtComplexClosure, sqrtRealClosure,
                  sqrtRealPosClosure)
        from proveit.numbers import (
                Complex, NaturalPos, RationalPos, Real, RealPos)

        if number_set == NaturalPos:
            return expNatClosure.instantiate({a:self.base, b:self.exponent},
                      assumptions=assumptions)

        if number_set == RationalPos:
            # if we have a^b with a Rational and b Integer
            # if b is proven to be any Integer

            # if we already know a^b is

            # if b = 0, then a^b = 1 (if a≠0)

            # to be continued later
            pass

        # the following would be useful to replace the next two Real
        # closure theorems, once we get the system to deal
        # effectively with the Or(A, And(B, C)) conditions
        # if number_set == Real:
        #     return expRealClosure.instantiate(
        #                     {a:self.base, b:self.exponent},
        #                     assumptions=assumptions)

        if number_set == Real:
            # Would prefer the more general approach commented-out
            # above; in the meantime, allowing for 2 possibilities here:
            # if base is positive real, exp can be any real;
            # if base is real ≥ 0, exp must be non-zero
            if self.exponent==frac(one, two):
                return sqrtRealClosure.instantiate(
                        {a:self.base},assumptions=assumptions)
            else:
                err_string = ''
                try:
                    return expRealClosureBasePos.instantiate(
                            {a:self.base, b:self.exponent},
                            assumptions=assumptions)
                except:
                    err_string = 'Positive base condition failed '
                    try:
                        return expRealClosureExpNonZero.instantiate(
                                {a:self.base, b:self.exponent},
                                assumptions=assumptions)
                    except:
                        err_string += (
                            'and non-zero exponent condition failed. '
                            'Need base ≥ 0 and exponent ≠ 0, OR base > 0.')
                        raise Exception(err_string)

        if number_set == RealPos:
            if self.exponent==frac(one, two):
                return sqrtRealPosClosure.instantiate(
                        {a:self.base},assumptions=assumptions)
            else:
                return expRealPosClosure.instantiate(
                        {a:self.base, b:self.exponent},assumptions=assumptions)

        if number_set == Complex:
            if self.exponent==frac(one, two):
                return sqrtComplexClosure.instantiate(
                        {a:self.base}, assumptions=assumptions)
            else:
                return expComplexClosure.instantiate(
                            {a:self.base, b:self.exponent},
                            assumptions=assumptions)

        msg = "'deduceInNumberSet' not implemented for the %s set"%str(number_set)
        raise ProofFailure(InSet(self, number_set), assumptions, msg)

    
class ExpSetMembership(Membership):
    '''
    Defines methods that apply to membership in an exponentiated set. 
    '''
    
    def __init__(self, element, domain):
        Membership.__init__(self, element)
        self.domain = domain

    def conclude(self, assumptions=USE_DEFAULTS):
        '''
        Attempt to conclude that the element is in the exponentiated set.
        '''   
        from proveit.logic import InSet
        from proveit.logic.sets.membership._theorems_ import (
            exp_set_0, exp_set_1, exp_set_2, exp_set_3, exp_set_4, exp_set_5,
            exp_set_6, exp_set_7, exp_set_8, exp_set_9)
        from proveit.numbers import zero, isLiteralInt, DIGITS
        element = self.element
        domain = self.domain
        elem_in_set = InSet(element, domain)
        if not isinstance(element, ExprTuple):
            raise ProofFailure(
                elem_in_set, assumptions,
                "Can only automatically deduce membership in exponentiated "
                "sets for an element that is a list")
        exponent_eval = domain.exponent.evaluation(assumptions=assumptions)
        exponent = exponent_eval.rhs
        base = domain.base
        #print(exponent, base, exponent.asInt(),element, domain, len(element))
        if isLiteralInt(exponent):
            if exponent == zero:
                return exp_set_0.instantiate({S:base}, assumptions=assumptions)
            if len(element) != exponent.asInt():
                raise ProofFailure(
                    elem_in_set, assumptions,
                    "Element not a member of the exponentiated set; "
                    "incorrect list length")
            elif exponent in DIGITS:
                # thm = forall_S forall_{a, b... in S} (a, b, ...) in S^n
                thm = locals()['exp_set_%d'%exponent.asInt()]
                expr_map = {S:base} # S is the base
                # map a, b, ... to the elements of element.
                expr_map.update({proveit._common_.__getattr__(chr(ord('a')+k)):elem_k for k, elem_k in enumerate(element)})
                elem_in_set = thm.instantiate(expr_map, assumptions=assumptions)
            else:
                raise ProofFailure(
                    elem_in_set, assumptions,
                    "Automatic deduction of membership in exponentiated sets "
                    "is not supported beyond an exponent of 9")
        else:
            raise ProofFailure(
                elem_in_set, assumptions,
                "Automatic deduction of membership in exponentiated sets is "
                "only supported for an exponent that is a literal integer")
        if exponent_eval.lhs != exponent_eval.rhs:
            # after proving that the element is in the set taken to
            # the evaluation of the exponent, substitute back in the
            # original exponent.
            return exponent_eval.subLeftSideInto(elem_in_set,
                                                 assumptions=assumptions)
        return elem_in_set

    def sideEffects(self, judgment):
        return
        yield

# outside any specific class:
# special Exp case of square root
def sqrt(base):
    '''
    Special function for square root version of an exponential.
    Formatting depends on the argument supplied to the withStyles()
    method called on the Expression superclass, which then sets
    things up so the Exp latex() method will display the expression
    using a traditional square root radical. If you want a square
    root to be displayed more literally as a base to the 1/2 power,
    use Exp(_, frac(1/2)) directly.
    Could later generalize this to cube roots or general nth roots.
    '''
    return Exp(base, frac(one, two)).withStyles(exponent='radical')

# Register these expression equivalence methods:
InnerExpr.register_equivalence_method(Exp, 'distribution', 'distributed', 'distribute')