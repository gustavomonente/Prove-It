import inspect
from proveit._core_.expression.expr import (
        Expression, MakeNotImplemented, free_vars)
from proveit._core_.expression.lambda_expr.lambda_expr import Lambda, getParamVar
from proveit._core_.expression.composite import (
        ExprTuple, singleOrCompositeExpression, compositeExpression,
        ExprRange)
from proveit._core_.expression.conditional import Conditional
from proveit._core_.defaults import USE_DEFAULTS
from .operation import Operation, OperationError
from .function import Function

def _extract_domain_from_condition(ivar, condition):
    '''
    Given a "domain" condition (e.g., "x in S" or "(x_1 in S), ..., (x_n in S)")
    return the domain (e.g., "S").  Return None if the condition is not
    a "domain" condition for the given instance variable(s).
    '''
    from proveit.logic import InSet
    if isinstance(ivar, ExprRange):
        if (isinstance(condition, ExprRange) and isinstance(condition.body, InSet)
                and condition.body.element==ivar.body
                and condition.start_index==ivar.start_index
                and condition.end_index==ivar.end_index):
            return condition.body.domain
    elif isinstance(condition, InSet) and condition.element==ivar:
        return condition.domain
    return None



class OperationOverInstances(Operation):
    '''
    OperationOverInstances description: TODO
    '''

    '''
    When deriving from OperationOverInstances, set the '_init_argname_mapping'
    static variable to indicate how the initialization argument names in the
    derived class correspond with the OperationOverInstances argument names.
    Omitted keys will be presumed to be unchanged argument names.  This is
    a simple way to make extractMyInitArgValue function properly without
    overriding it.
    '''
    _init_argname_mapping_ = {'instanceParamOrParams':'instanceParamOrParams', 'instanceExpr':'instanceExpr', 'domain':'domain', 'domains':'domains', 'conditions':'conditions'}

    def __init__(self, operator, instanceParamOrParams, instanceExpr, *,
                 domain=None, domains=None, condition=None, conditions=None,
                 styles=None, _lambda_map=None):
        '''
        Create an Operation for the given operator that is applied over
        instances of the given instance parameter(s), instanceParamOrParams,
        for the given instance Expression,  instanceExpr under the given
        conditions.  That is, the operation operates over all possibilities of
        given Variable(s) wherever the condition(s) is/are satisfied.  Examples
        include forall, exists, summation, etc. instanceParamOrParams may be
        singular or plural (iterable).  Each parameter may be a Variable or
        Iter over IndexedVars (just as a Lambda parameter).  An
        OperationOverInstances is effected as an Operation over a Lambda map
        with a conditional body.

        If a 'domain' is supplied, additional conditions are generated that
        each instance parameter is in the domain "set": InSet(x_i, domain),
        where x_i is for each instance parameter.  If, instead, 'domains' are
        supplied, then each instance parameter is supplied with its own domain
        (one for each instance parameter).  Whether the OperationOverInstances
        is constructed with domain/domains explicitly, or they are provided as
        conditions in the proper order does not matter.  Essentially, the
        'domain' concept is simply a convenience for conditions of this form
        and may be formatted using a shorthand notation.
        For example, "forall_{x in S | Q(x)} P(x)" is a shorthand notation for
        "forall_{x | x in S, Q(x)} P(x)".

        _lambda_map is used internally for efficiently rebuilding an
        OperationOverInstances expression.
        '''
        from proveit.logic import InSet
        from proveit._core_.expression.lambda_expr.lambda_expr import getParamVar

        if styles is None: styles=dict()
        if condition is not None:
            if conditions is not None:
                raise ValueError("Cannot specify both 'conditions' and "
                                 "'condition'")
            conditions = (condition,)
        elif conditions is None:
            conditions = tuple()

        if _lambda_map is not None:
            # Use the provided 'lambda_map' instead of creating one.
            from proveit.logic import And
            lambda_map = _lambda_map
            instance_params = lambda_map.parameters
            if isinstance(lambda_map.body, Conditional):
                # Has conditions.
                instanceExpr = lambda_map.body.value
                if (isinstance(lambda_map.body.condition, And) and
                        not lambda_map.body.condition.operands.singular()):
                    conditions = compositeExpression(lambda_map.body.condition.operands)
                else:
                    conditions = compositeExpression(lambda_map.body.condition)
            else:
                # No conditions.
                instanceExpr = lambda_map.body
                conditions = ExprTuple()
        else:
            # We will need to generate the Lambda sub-expression.
            # Do some initial preparations w.r.t. instanceParams, domain(s), and
            # conditions.
            instance_params = compositeExpression(instanceParamOrParams)
            if len(instance_params)==0:
                raise ValueError("Expecting at least one instance parameter when "
                                 "constructing an OperationOverInstances")

            # Add appropriate conditions for the domains:
            if domain is not None:
                # prepend domain conditions
                if domains is not None:
                    raise ValueError("Provide a single domain or multiple domains, "
                                     "not both")
                if not isinstance(domain, Expression):
                    raise TypeError("The domain should be an 'Expression' type")
                domains = [domain]*len(instance_params)

            if domains is not None:
                # Prepend domain conditions.  Note that although we start with
                # all domain conditions at the beginning,
                # some may later get pushed back as "inner conditions"
                # (see below),
                if len(domains) != len(instance_params):
                    raise ValueError("When specifying multiple domains, the number "
                                     "should be the same as the number of instance "
                                     "variables.")
                for domain in domains:
                    if domain is None:
                        raise ValueError("When specifying multiple domains, none "
                                         "of them can be the None value")
                domain_conditions = []
                for iparam, domain in zip(instance_params, domains):
                    if isinstance(iparam, ExprRange):
                        condition = ExprRange(
                                iparam.parameter, InSet(iparam.body, domain),
                                iparam.start_index, iparam.end_index)
                    else:
                        condition = InSet(iparam, domain)
                    domain_conditions.append(condition)
                conditions = domain_conditions + list(conditions)
                domain = domains[0] # domain of the outermost instance variable
            conditions = compositeExpression(conditions)

        # domain(s) may be implied via the conditions.  If domain(s) were
        # supplied, this should simply reproduce them from the conditions that
        # were prepended.
        domain = domains = None # These may be reset below if there are ...
        if (len(conditions)>=len(instance_params)):
            domains = [_extract_domain_from_condition(ivar, cond) for
                       ivar, cond in zip(instance_params, conditions)]
            if all(domain is not None for domain in domains):
                # Used if we have a single instance variable
                domain = domains[0]
            else: domains=None

        if _lambda_map is None:
            # Now do the actual lambda_map creation
            if len(instance_params)==1:
                instanceParamOrParams = instance_params[0]
            # Generate the Lambda sub-expression.
            lambda_map = OperationOverInstances._createOperand(instanceParamOrParams,
                                                               instanceExpr,
                                                               conditions)

        self.instanceExpr = instanceExpr
        '''Expression corresponding to each 'instance' in the OperationOverInstances'''

        self.instanceParams = instance_params
        if len(instance_params) > 1:
            '''Instance parameters of the OperationOverInstance.'''
            self.instanceVars = [getParamVar(parameter) for
                                 parameter in instance_params]
            self.instanceParamOrParams = self.instanceParams
            self.instanceVarOrVars = self.instanceVars
            '''Instance parameter variables of the OperationOverInstance.'''
            if domains is not None:
                self.domains = domains # Domain for each instance variable
                '''Domains of the instance parameters (may be None)'''
            else:
                self.domain = None
        else:
            self.instanceParam = instance_params[0]
            '''Outermost instance parameter of the OperationOverInstance.'''
            self.instanceVar = getParamVar(self.instanceParam)
            self.instanceParamOrParams = self.instanceParam
            self.instanceVarOrVars = self.instanceVar
            '''Outermost instance parameter variable of the OperationOverInstance.'''
            self.domain = domain
            '''Domain of the outermost instance parameter (may be None)'''

        self.conditions = conditions
        '''Conditions applicable to the outermost instance variable (or iteration of indexed variables) of the OperationOverInstance.  May include an implicit 'domain' condition.'''

        if isinstance(lambda_map.body, Conditional):
            self.condition = lambda_map.body.condition

        Operation.__init__(self, operator, lambda_map, styles=styles)

    def effectiveCondition(self):
        '''
        Return the effective 'condition' of the OperationOverInstances.
        If there is no 'condition', return And operating on zero
        operands.
        '''
        if hasattr(self, 'condition'):
            return self.condition
        else:
            from proveit.logic import And
            return And()

    def hasDomain(self):
        if hasattr(self, 'domains'):
            return self.domains is not None
        return self.domain is not None

    def first_domain(self):
        if hasattr(self, 'domains'):
            return self.domains[0]
        return self.domain

    @staticmethod
    def _createOperand(instanceParamOrParams, instanceExpr, conditions):
        if len(conditions) == 0:
            return Lambda(instanceParamOrParams, instanceExpr)
        else:
            conditional =  Conditional(instanceExpr, conditions)
            return Lambda(instanceParamOrParams, conditional)

    def extractMyInitArgValue(self, argName):
        '''
        Return the most proper initialization value for the
        initialization argument of the given name in order to
        reconstruct this Expression in its current style.
        '''
        init_argname_mapping = self.__class__._init_argname_mapping_
        argName = init_argname_mapping.get(argName, argName)
        if argName=='operator':
            return self.operator # simply the operator
        elif argName=='instanceParamOrParams':
            # return the joined instance variables according to style.
            return singleOrCompositeExpression(
                OperationOverInstances.explicitInstanceParams(self))
        elif argName=='instanceExpr':
            # return the inner instance expression after joining the
            # instance variables according to the style
            return self.instanceExpr
        elif argName=='domain' or argName=='domains':
            # return the proper single domain or list of domains
            domains = OperationOverInstances.explicitDomains(self)
            if not hasattr(self, 'domain') or domains != [self.domain]*len(domains):
                return ExprTuple(*domains) if argName=='domains' else None
            if self.domain is None: return None
            return self.domain if argName=='domain' else None
        elif argName=='condition' or argName=='conditions':
            # return the joined conditions excluding domain conditions
            conditions = compositeExpression(
                OperationOverInstances.explicitConditions(self))
            if len(conditions)==1 and argName=='condition':
                return conditions[0]
            elif len(conditions) > 1 and argName=='conditions':
                return conditions
            return None

    @classmethod
    def _make(cls, coreInfo, styles, subExpressions):
        if len(coreInfo) != 1 or coreInfo[0] != 'Operation':
            raise ValueError("Expecting Operation coreInfo to contain exactly one item: 'Operation'")
        if len(subExpressions) != 2:
            raise ValueError("Expecting exactly two subExpressions for an "
                             "OperationOverInstances object: an operator and "
                             "a lambda_map.")

        implicit_operator = cls._implicitOperator()
        if implicit_operator is None:
            raise OperationError("Expecting a '_operator_' attribute for class "
                                 "%s for the default OperationOverInstances._make "
                                 "method"%str(cls))

        operator = subExpressions[0]
        lambda_map = subExpressions[1]

        if not (operator == implicit_operator):
            raise OperationError("An implicit operator may not be changed")

        args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, _ = \
            inspect.getfullargspec(cls.__init__)
        if '_lambda_map' not in kwonlyargs:
            raise OperationError("'_lambda_map' must be a keyword only argument "
                                 "for a constructor of a class %s derived from "
                                 "OperationOverInstances."%str(cls))

        # Subtract 'self' from the number of args and set
        # the rest to None.
        num_remaining_args = len(args)-1
        made_operation = cls(*[None]*num_remaining_args, _lambda_map=lambda_map)
        if styles is not None:
            made_operation.withStyles(**styles)
        return made_operation

    def _allInstanceParams(self):
        '''
        Yields the instance parameters (each a Variable or Iter of IndexedVars)
        of this OperationOverInstances and any instance parameters of nested
        OperationOverInstances.
        '''
        if hasattr(self, 'instanceParams'):
            for ivar in self.instanceParams:
                yield ivar
        else:
            yield self.instanceParam
        if isinstance(self.instanceExpr, self.__class__):
            for innerIvar in self.instanceExpr._allInstanceParams():
                yield innerIvar

    def allInstanceParams(self):
        '''
        Returns all instance parameters (each a Variable or Iter of
        IndexedVars) of this OperationOverInstances
        and all instance parameters of nested OperationOverInstances.
        '''
        return list(self._allInstanceParams())

    def _allInstanceVars(self):
        '''
        Yields the instance parameter variable of this OperationOverInstances
        and any instance parameter variables of nested OperationOverInstances
        of the same type.
        '''
        if hasattr(self, 'instanceVars'):
            for ivar in self.instanceVars:
                yield ivar
        else:
            yield self.instanceVar
        if isinstance(self.instanceExpr, self.__class__):
            for innerIvar in self.instanceExpr._allInstanceVars():
                yield innerIvar

    def allInstanceVars(self):
        '''
        Returns all instance parameter variables of this OperationOverInstances
        and all instance parameters variables of nested OperationOverInstances.
        '''
        return list(self._allInstanceVars())

    def _allDomains(self):
        '''
        Yields the domain of this OperationOverInstances
        and any domains of nested OperationOVerInstances
        of the same type.  Some of these may be null.
        Modified by wdc on 6/17/2019, modifying generator fxn name
        from alldomains() to _alldomains() and adding a separate
        non-generator version of the alldomains() fxn below.
        '''
        if hasattr(self, 'domains'):
            for domain in self.domains:
                yield domain
        else:
            yield self.domain
            if isinstance(self.instanceExpr, self.__class__):
                for domain in self.instanceExpr.allDomains():
                    yield domain

    def allDomains(self):
        '''
        Returns all domains of this OperationOverInstances
        including domains of nested OperationOverInstances
        of the same type.
        '''
        return list(self._allDomains())

    def _allConditions(self):
        '''
        Yields each condition of this OperationOverInstances
        and any conditions of nested OperationOverInstances
        of the same type.
        Modified by wdc on 6/06/2019, modifying generator fxn name
        from allConditions() to _allConditions() and adding a separate
        non-generator version of the allConditions() fxn below.
        '''
        for condition in self.conditions:
            yield condition
        if isinstance(self.instanceExpr, self.__class__):
            for condition in self.instanceExpr.allConditions():
                yield condition

    def allConditions(self):
        '''
        Returns all conditions of this OperationOverInstances
        and all conditions of nested OperationOverInstances
        of the same type. Relies on the Python generator function
        _allConditions() defined above.
        Added by wdc on 6/06/2019.
        '''
        return list(self._allConditions())

    def explicitInstanceParams(self):
        '''
        Return the instance parameters that are to be shown explicitly
        in the formatting (as opposed to being made implicit via
        conditions) joined together at this level according to the
        style. By default, this includes all of the instance parameters
        that are to be joined but this may be overridden to exclude
        implicit instance parameters.
        '''
        if hasattr(self, 'instanceParams'):
            return self.instanceParams
        else:
            return [self.instanceParam]

    def explicitInstanceVars(self):
        '''
        Return the instance parameter variables that are to be shown explicitly
        in the formatting (as opposed to being made implicit via conditions)
        joined together at this level according to the style. The behavior
        is determined by 'explicitInstanceParams'.  Here, we simply extract
        the variables from the parameters that result from
        'explicitInstanceParams'.
        '''
        return [getParamVar(parameter) for
                parameter in self.explicitInstanceParams()]

    def explicitDomains(self):
        '''
        Return the domains of the instance variables that
        are joined together at this level according to the style.
        If there is no domain, return None.
        '''
        if not self.hasDomain():
            return []
        if hasattr(self, 'domains'):
            return self.domains
        elif self.domain is not None:
            return [self.domain]
        return [] # No explicitly displayed domains

    def domainConditions(self):
        '''
        Return the domain conditions of all instance variables that
        areg joined together at this level according to the style.
        '''
        if hasattr(self, 'domains'):
            assert len(self.conditions) >= len(self.domains), 'expecting a condition for each domain'
            for iparam, condition, domain in  \
                    zip(self.instanceParams, self.conditions, self.domains):
                assert domain == _extract_domain_from_condition(iparam, condition)
            return self.conditions[:len(self.domains)]
        else:
            explicit_domains = self.explicitDomains()
            if len(explicit_domains)==0:
                return [] # no explicit domains
            domain_conditions = []
            assert (self.domain ==
                    _extract_domain_from_condition(self.instanceParam,
                                                   self.conditions[0]))
            domain_conditions.append(self.conditions[0])
            return domain_conditions

    def explicitConditions(self):
        '''
        Return the conditions that are to be shown explicitly in the formatting
        (after the "such that" symbol "|") at this level according to the
        style.  By default, this includes all of the 'joined' conditions except
        implicit 'domain' conditions.
        '''
        if hasattr(self, 'domains'):
            assert len(self.conditions) >= len(self.domains), ('expecting a condition'
                                                               ' for each domain')
            for iparam, condition, domain in zip(self.instanceParams, self.conditions,
                                                self.domains):
                cond_domain = _extract_domain_from_condition(iparam, condition)
                assert cond_domain == domain
            return self.conditions[len(self.domains):] # skip the domains
        else:
            explicit_domains = self.explicitDomains()
            conditions = []
            if len(explicit_domains)==0:
                conditions.extend(self.conditions)
            else:
                cond_domain = _extract_domain_from_condition(self.instanceParam,
                                                             self.conditions[0])
                assert cond_domain == self.domain
                conditions.extend(self.conditions[1:])
            return conditions

    def _instanceParamLists(self):
        '''
        Yield lists of instance vars that include all of the instance
        paramaters (see allInstanceParams method) but grouped together
        according to the style joining instance variables together.
        '''
        expr = self
        while isinstance(expr, self.__class__):
            if hasattr(expr, 'instanceParams'):
                yield expr.instanceParams # grouped together
            else:
                yield [expr.instanceParam]
            expr = expr.instanceExpr

    def instanceParamLists(self):
        '''
        Returns lists of instance parameters that include all of the instance
        parameters (see allInstanceParams method) but grouped together
        according to the style joining instance parameters together.
        '''
        return list(self._instanceParamLists())

    def string(self, **kwargs):
        return self._formatted('string', **kwargs)

    def latex(self, **kwargs):
        return self._formatted('latex', **kwargs)

    def _formatted(self, formatType, fence=False):
        '''
        Format the OperationOverInstances according to the style
        which may join nested operations of the same type.
        '''
        # override this default as desired
        explicitIparams = list(self.explicitInstanceParams())
        explicitConditions = ExprTuple(*self.explicitConditions())
        explicitDomains = ExprTuple(*self.explicitDomains())
        instanceExpr = self.instanceExpr
        hasExplicitIparams = (len(explicitIparams) > 0)
        hasExplicitConditions = (len(explicitConditions) > 0)
        hasMultiDomain = (len(explicitDomains)>1 and (not hasattr(self, 'domain')
                          or explicitDomains != ExprTuple(*[self.domain]*len(explicitDomains))))
        domain_conditions = ExprTuple(*self.domainConditions())
        outStr = ''
        formattedParams = ', '.join([param.formatted(formatType, abbrev=True)
                                     for param in explicitIparams])
        if formatType == 'string':
            if fence: outStr += '['
            outStr += self.operator.formatted(formatType) + '_{'
            if hasExplicitIparams:
                if hasMultiDomain: outStr += domain_conditions.formatted(formatType, operatorOrOperators=',', fence=False)
                else: outStr += formattedParams
            if not hasMultiDomain and self.domain is not None:
                outStr += ' in '
                if hasMultiDomain:
                    outStr += explicitDomains.formatted(formatType, operatorOrOperators='*', fence=False)
                else:
                    outStr += self.domain.formatted(formatType, fence=False)
            if hasExplicitConditions:
                if hasExplicitIparams: outStr += " | "
                outStr += explicitConditions.formatted(formatType, fence=False)
                #outStr += ', '.join(condition.formatted(formatType) for condition in self.conditions if condition not in implicitConditions)
            outStr += '} ' + instanceExpr.formatted(formatType,fence=True)
            if fence: outStr += ']'
        if formatType == 'latex':
            if fence: outStr += r'\left['
            outStr += self.operator.formatted(formatType) + '_{'
            if hasExplicitIparams:
                if hasMultiDomain: outStr += domain_conditions.formatted(formatType, operatorOrOperators=',', fence=False)
                else: outStr += formattedParams
            if not hasMultiDomain and self.domain is not None:
                outStr += r' \in '
                outStr += self.domain.formatted(formatType, fence=False)
            if hasExplicitConditions:
                if hasExplicitIparams: outStr += "~|~"
                outStr += explicitConditions.formatted(formatType, fence=False)
                #outStr += ', '.join(condition.formatted(formatType) for condition in self.conditions if condition not in implicitConditions)
            outStr += '}~' + instanceExpr.formatted(formatType,fence=True)
            if fence: outStr += r'\right]'

        return outStr

    """
    def instanceSubstitution(self, universality, assumptions=USE_DEFAULTS):
        '''
        Equate this OperationOverInstances, Upsilon_{..x.. in S | ..Q(..x..)..} f(..x..),
        with one that substitutes instance expressions given some
        universality = forall_{..x.. in S | ..Q(..x..)..} f(..x..) = g(..x..).
        Derive and return the following type of equality assuming universality:
        Upsilon_{..x.. in S | ..Q(..x..)..} f(..x..) = Upsilon_{..x.. in S | ..Q(..x..)..} g(..x..)
        Works also when there is no domain S and/or no conditions ..Q...
        '''
        from proveit.logic.equality._axioms_ import instanceSubstitution, noDomainInstanceSubstitution
        from proveit.logic import Forall, Equals
        from proveit import KnownTruth
        from proveit._common_ import n, Qmulti, xMulti, yMulti, zMulti, f, g, Upsilon, S
        if isinstance(universality, KnownTruth):
            universality = universality.expr
        if not isinstance(universality, Forall):
            raise InstanceSubstitutionException("'universality' must be a forall expression", self, universality)
        if len(universality.instanceVars) != len(self.instanceVars):
            raise InstanceSubstitutionException("'universality' must have the same number of variables as the OperationOverInstances having instances substituted", self, universality)
        if universality.domain != self.domain:
            raise InstanceSubstitutionException("'universality' must have the same domain as the OperationOverInstances having instances substituted", self, universality)
        # map from the forall instance variables to self's instance variables
        iVarSubstitutions = {forallIvar:selfIvar for forallIvar, selfIvar in zip(universality.instanceVars, self.instanceVars)}
        if universality.conditions.substituted(iVarSubstitutions) != self.conditions:
            raise InstanceSubstitutionException("'universality' must have the same conditions as the OperationOverInstances having instances substituted", self, universality)
        if not isinstance(universality.instanceExpr, Equals):
            raise InstanceSubstitutionException("'universality' must be an equivalence within Forall: " + str(universality))
        if universality.instanceExpr.lhs.substituted(iVarSubstitutions) != self.instanceExpr:
            raise InstanceSubstitutionException("lhs of equivalence in 'universality' must match the instance expression of the OperationOverInstances having instances substituted", self, universality)
        f_op, f_op_sub = Operation(f, self.instanceVars), self.instanceExpr
        g_op, g_op_sub = Operation(g, self.instanceVars), universality.instanceExpr.rhs.substituted(iVarSubstitutions)
        Q_op, Q_op_sub = Operation(Qmulti, self.instanceVars), self.conditions
        if self.hasDomain():
            return instanceSubstitution.specialize({Upsilon:self.operator, Q_op:Q_op_sub, S:self.domain, f_op:f_op_sub, g_op:g_op_sub},
                                                    relabelMap={xMulti:universality.instanceVars, yMulti:self.instanceVars, zMulti:self.instanceVars}, assumptions=assumptions).deriveConsequent(assumptions=assumptions)
        else:
            return noDomainInstanceSubstitution.specialize({Upsilon:self.operator, Q_op:Q_op_sub, f_op:f_op_sub, g_op:g_op_sub},
                                                             relabelMap={xMulti:universality.instanceVars, yMulti:self.instanceVars, zMulti:self.instanceVars}, assumptions=assumptions).deriveConsequent(assumptions=assumptions)

    def substituteInstances(self, universality, assumptions=USE_DEFAULTS):
        '''
        Assuming this OperationOverInstances, Upsilon_{..x.. in S | ..Q(..x..)..} f(..x..)
        to be a true statement, derive and return Upsilon_{..x.. in S | ..Q(..x..)..} g(..x..)
        given some 'universality' = forall_{..x.. in S | ..Q(..x..)..} f(..x..) = g(..x..).
        Works also when there is no domain S and/or no conditions ..Q...
        '''
        substitution = self.instanceSubstitution(universality, assumptions=assumptions)
        return substitution.deriveRightViaEquivalence(assumptions=assumptions)
    """

def bundle(expr, bundle_thm, num_levels=2, *, assumptions=USE_DEFAULTS):
    '''
    Given a nested OperationOverInstances, derive or equate an
    equivalent form in which a given number of nested levels is
    bundled together.  Use the given theorem specific to the particular
    OperationOverInstances.

    For example,
        \forall_{x, y | Q(x, y)} \forall_{z | R(z)} P(x, y, z)
    can become
        \forall_{x, y, z | Q(x, y), R(z)} P(x, y, z)
    via bundle with num_levels=2.

    For example of the form of the theorem required, see
    proveit.logic.boolean.quantification.bundling or
    proveit.logic.boolean.quantification.bundling_equality.
    '''
    from proveit.relation import TransRelUpdater
    from proveit.logic import Implies, Equals
    # Make a TransRelUpdater only if the bundle_thm yield an
    # equation, in which case we'll want the result to be an equation.
    eq = None
    bundled = expr
    while num_levels >= 2:
        if (not isinstance(bundled, OperationOverInstances) or
                not isinstance(bundled.instanceExpr, OperationOverInstances)):
            raise ValueError("May only 'bundle' nested OperationOverInstances, "
                             "not %s"%bundled)
        _m = bundled.instanceParams.length()
        _n = bundled.instanceExpr.instanceParams.length()
        _P = bundled.instanceExpr.instanceExpr
        _Q = bundled.effectiveCondition()
        _R = bundled.instanceExpr.effectiveCondition()
        m, n = bundle_thm.instanceVars
        P, Q, R = bundle_thm.instanceExpr.instanceVars
        correspondence = bundle_thm.instanceExpr.instanceExpr
        if isinstance(correspondence, Implies):
            if (not isinstance(correspondence.antecedent,
                               OperationOverInstances)
                    or not len(correspondence.consequent.instanceParams)==2):
                raise ValueError("'bundle_thm', %s, does not have the "
                                 "expected form with the bundled form as "
                                 "the consequent of the implication, %s"
                                 %(bundle_thm, correspondence))
            x_1_to_m, y_1_to_n = correspondence.consequent.instanceParams
        elif isinstance(correspondence, Equals):
            if not isinstance(correspondence.rhs, OperationOverInstances
                    or not len(correspondence.antecedent.instanceParams)==2):
                raise ValueError("'bundle_thm', %s, does not have the "
                                 "expected form with the bundled form on "
                                 "right of the an equality, %s"
                                 %(bundle_thm, correspondence))
            x_1_to_m, y_1_to_n = correspondence.rhs.instanceParams

        all_params = bundled.instanceParams + bundled.instanceExpr.instanceParams
        Pxy = Function(P, all_params)
        Qx = Function(Q, bundled.instanceParams)
        Rxy = Function(R, all_params)
        x_1_to_m = x_1_to_m.replaced({m:_m})
        y_1_to_n = y_1_to_n.replaced({n:_n})
        instantiation = bundle_thm.instantiate(
                {m:_m, n:_n, ExprTuple(x_1_to_m):bundled.instanceParams,
                 ExprTuple(y_1_to_n):bundled.instanceExpr.instanceParams ,
                 Pxy:_P, Qx:_Q, Rxy:_R}, assumptions=assumptions)
        if isinstance(instantiation.expr, Implies):
            bundled = instantiation.deriveConsequent()
        elif isinstance(instantiation.expr, Equals):
            if eq is None:
                eq = TransRelUpdater(bundled)
            try:
                bundled = eq.update(instantiation)
            except ValueError:
                raise ValueError(
                        "Instantiation of bundle_thm %s is %s but "
                        "should match %s on one side of the equation."
                        %(bundle_thm, instantiation, bundled))
        else:
            raise ValueError("Instantiation of bundle_thm %s is %s but "
                             "should be an Implies or Equals expression."
                             %(bundle_thm, instantiation))
        num_levels -= 1
    if eq is None:
        # Return the bundled result.
        return bundled
    else:
        # Return the equality between the original expression and
        # the bundled result.
        return eq.relation

def unbundle(expr, unbundle_thm, num_param_entries=(1,), *,
             assumptions=USE_DEFAULTS):
    '''
    Given a nested OperationOverInstances, derive or equate an
    equivalent form in which the parameter entries are split in
    number according to 'num_param_entries'.  Use the given theorem
    specific to the particular OperationOverInstances.

    For example,
        \forall_{x, y, z | Q(x, y), R(z)} P(x, y, z)
    can become
        \forall_{x, y | Q(x, y)} \forall_{z | R(z)} P(x, y, z)
    via bundle with num_param_entries=(2, 1) or
    num_param_entries=(2,) -- the last number can be implied
    by the remaining number of parameters.

    For example of the form of the theorem required, see
    proveit.logic.boolean.quantification.unbundling or
    proveit.logic.boolean.quantification.bundling_equality.
    '''
    from proveit.relation import TransRelUpdater
    from proveit.logic import Implies, Equals, And
    # Make a TransRelUpdater only if the bundle_thm yield an
    # equation, in which case we'll want the result to be an equation.
    eq = None
    unbundled = expr
    net_indicated_param_entries = sum(num_param_entries)
    num_actual_param_entries = len(expr.instanceParams)
    for n in num_param_entries:
        if not isinstance(n, int) or n <= 0:
            raise ValueError(
                    "Each of 'num_param_entries', must be an "
                    "integer greater than 0.  %s fails this requirement."
                    %(num_param_entries))
    if net_indicated_param_entries > num_actual_param_entries:
        raise ValueError("Sum of 'num_param_entries', %s=%d should not "
                         "be greater than the number of parameter entries "
                         "of %s for unbundling."
                         %(num_param_entries, net_indicated_param_entries,
                           expr))
    if net_indicated_param_entries < num_actual_param_entries:
        diff = num_actual_param_entries - net_indicated_param_entries
        num_param_entries = list(num_param_entries) + [diff]
    else:
        num_param_entries = list(num_param_entries)
    while len(num_param_entries) > 1:
        n_last_entries = num_param_entries.pop(-1)
        first_params = ExprTuple(*unbundled.instanceParams[:-n_last_entries])
        first_param_vars = {getParamVar(param) for param in first_params}
        remaining_params = \
            ExprTuple(*unbundled.instanceParams[-n_last_entries:])
        _m = first_params.length()
        _n = remaining_params.length()
        _P = unbundled.instanceExpr
        # Split up the conditions between the outer
        # OperationOverInstances and inner OperationOverInstances
        condition = unbundled.effectiveCondition()
        if isinstance(condition, And):
            _nQ = 0
            for cond in condition.operands:
                cond_vars = free_vars(cond, err_inclusively=True)
                if first_param_vars.isdisjoint(cond_vars): break
                _nQ += 1
            if _nQ == 0:
                _Q = And()
            elif _nQ == 1:
                _Q = condition.operands[0]
            else:
                _Q = And(*condition.operands[:_nQ])
            _nR = len(condition.operands) - _nQ
            if _nR == 0:
                _R = And()
            elif _nR == 1:
                _R = condition.operands[-1]
            else:
                _R = And(*condition.operands[_nQ:])
        elif first_param_vars.isdisjoint(free_vars(condition,
                                                   err_inclusively=True)):
            _Q = condition
            _R = And()
        else:
            _Q = And()
            _R = condition
        m, n = unbundle_thm.instanceVars
        P, Q, R = unbundle_thm.instanceExpr.instanceVars
        correspondence = unbundle_thm.instanceExpr.instanceExpr
        if isinstance(correspondence, Implies):
            if (not isinstance(correspondence.antecedent,
                               OperationOverInstances)
                    or not len(correspondence.antecedent.instanceParams)==2):
                raise ValueError("'unbundle_thm', %s, does not have the "
                                 "expected form with the bundled form as "
                                 "the antecedent of the implication, %s"
                                 %(unbundle_thm, correspondence))
            x_1_to_m, y_1_to_n = correspondence.antecedent.instanceParams
        elif isinstance(correspondence, Equals):
            if not isinstance(correspondence.rhs, OperationOverInstances
                    or not len(correspondence.antecedent.instanceParams)==2):
                raise ValueError("'unbundle_thm', %s, does not have the "
                                 "expected form with the bundled form on "
                                 "right of the an equality, %s"
                                 %(unbundle_thm, correspondence))
            x_1_to_m, y_1_to_n = correspondence.rhs.instanceParams
        else:
            raise ValueError("'unbundle_thm', %s, does not have the expected "
                             "form with an equality or implication  "
                             "correspondence, %s"
                             %(unbundle_thm, correspondence))

        Qx = Function(Q, first_params)
        Rxy = Function(R, unbundled.instanceParams)
        Pxy = Function(P, unbundled.instanceParams)
        x_1_to_m = x_1_to_m.replaced({m:_m})
        y_1_to_n = y_1_to_n.replaced({n:_n})
        instantiation = unbundle_thm.instantiate(
                {m:_m, n:_n, ExprTuple(x_1_to_m):first_params,
                 ExprTuple(y_1_to_n):remaining_params,
                 Pxy:_P, Qx:_Q, Rxy:_R}, assumptions=assumptions)
        if isinstance(instantiation.expr, Implies):
            unbundled = instantiation.deriveConsequent()
        elif isinstance(instantiation.expr, Equals):
            if eq is None:
                eq = TransRelUpdater(unbundled)
            try:
                unbundled = eq.update(instantiation)
            except ValueError:
                raise ValueError(
                        "Instantiation of bundle_thm %s is %s but "
                        "should match %s on one side of the equation."
                        %(unbundle_thm, instantiation, unbundled))
        else:
            raise ValueError("Instantiation of bundle_thm %s is %s but "
                             "should be an Implies or Equals expression."
                             %(unbundle_thm, instantiation))
    if eq is None:
        # Return the unbundled result.
        return unbundled
    else:
        # Return the equality between the original expression and
        # the unbundled result.
        return eq.relation

class InstanceSubstitutionException(Exception):
    def __init__(self, msg, operationOverInstances, universality):
        self.msg = msg
        self.operationOverInstances = operationOverInstances
        self.universality = universality
    def __str__(self):
        return self.msg + '.\n  operationOverInstances: ' + str(self.operationOverInstances) + '\n  universality: ' + str(self.universality)
