import inspect
from proveit._core_.expression.expr import Expression, ImproperReplacement
from proveit._core_.expression.style_options import StyleOptions
from proveit._core_.defaults import USE_DEFAULTS


class Operation(Expression):
    # Map _operator_ Literals to corresponding Operation classes.
    # This is populated automatically when the _operator_ attribute
    # is accessed (see ExprType in proveit._core_.expression.expr).
    operation_class_of_operator = dict()

    @staticmethod
    def _clear_():
        '''
        Clear all references to Prove-It information under
        the Expression jurisdiction.  All Expression classes that store
        Prove-It state information must implement _clear_ to clear that
        information.
        '''
        Operation.operation_class_of_operator.clear()

    def __init__(
            self,
            operator_or_operators,
            operand_or_operands,
            styles=None):
        '''
        Create an operation with the given operator(s) and operand(s).
        The operator(s) must be Label(s) (a Variable or a Literal).
        When there is a single operator, there will be an 'operator'
        attribute.  When there is a single operand, there will be
        an 'operand' attribute.  In any case, there will be
        'operators' and 'operands' attributes that bundle
        the one or more Expressions into a composite Expression.
        '''
        from proveit._core_.expression.composite import (
            Composite, composite_expression,
            single_or_composite_expression, ExprTuple, ExprRange)
        from proveit._core_.expression.label.label import Label
        from .indexed_var import IndexedVar
        if styles is None:
            styles = dict()
        if hasattr(
                self.__class__,
                '_operator_') and operator_or_operators == self.__class__._operator_:
            operator = operator_or_operators
            # if Expression.theories[operator._style_id] != operator.theory:
            #    raise OperationError("Expecting '_operator_' Theory to match the Theory of the Operation sub-class.  Use 'theory=__file__'.")
        if isinstance(operator_or_operators, ExprRange):
            operator_or_operators = [operator_or_operators]
        if isinstance(operand_or_operands, ExprRange):
            operand_or_operands = [operand_or_operands]
        self.operator_or_operators = single_or_composite_expression(
            operator_or_operators)

        # Reduce to a single operand if it is just a tuple with
        # one non-ExprRange and non-ExprTuple element.
        self.operand_or_operands = single_or_composite_expression(
            operand_or_operands, do_singular_reduction=True)

        def raise_bad_operator_type(operator):
            raise TypeError('operator(s) must be a Label, an indexed variable '
                            '(IndexedVar), or ranges of indexed'
                            'variables (IndexedVar). %s is none of those.'
                            % str(operator))
        if isinstance(self.operator_or_operators, Composite):
            # a composite of multiple operators:
            self.operators = self.operator_or_operators
            for operator in self.operators:
                if isinstance(operator, ExprRange):
                    if not isinstance(operator.body, IndexedVar):
                        raise_bad_operator_type(operator)
                elif not isinstance(operator, Label) and not isinstance(operator, IndexedVar):
                    raise_bad_operator_type(operator)
        else:
            # a single operator
            self.operator = self.operator_or_operators
            if not isinstance(
                    self.operator,
                    Label) and not isinstance(
                    self.operator,
                    IndexedVar):
                raise_bad_operator_type(self.operator)
            # wrap a single operator in a composite for convenience
            self.operators = composite_expression(self.operator)
        if isinstance(self.operand_or_operands, Composite):
            # a composite of multiple operands
            self.operands = self.operand_or_operands
            if (isinstance(self.operands, ExprTuple) and self.operands.num_entries()
                    == 1 and isinstance(self.operands[0], ExprTuple)):
                # This is a single operand that is an ExprTuple.
                self.operand = self.operands[0]
        else:
            # a single operand
            self.operand = self.operand_or_operands
            # wrap a single operand in a composite for convenience
            self.operands = composite_expression(self.operand)
        if 'operation' not in styles:
            styles['operation'] = 'infix'  # vs 'function'
        if 'wrap_positions' not in styles:
            styles['wrap_positions'] = '()'  # no wrapping by default
        if 'justification' not in styles:
            styles['justification'] = 'center'
        sub_exprs = (self.operator_or_operators, self.operand_or_operands)
        if isinstance(self, IndexedVar):
            core_type = 'IndexedVar'
        else:
            core_type = 'Operation'
        Expression.__init__(self, [core_type], sub_exprs, styles=styles)

    def style_options(self):
        options = StyleOptions(self)
        options.add_option('operation',
                           ("'infix' or 'function' style formatting"))
        options.add_option(
            'wrap_positions',
            ("position(s) at which wrapping is to occur; '2 n - 1' "
             "is after the nth operand, '2 n' is after the nth "
             "operation."))
        options.add_option(
            'justification',
            ("if any wrap positions are set, justify to the 'left', "
             "'center', or 'right'"))
        return options

    def with_wrapping_at(self, *wrap_positions):
        return self.with_styles(
            wrap_positions='(' +
            ' '.join(
                str(pos) for pos in wrap_positions) +
            ')')

    def with_wrap_before_operator(self):
        if self.operands.num_entries() != 2:
            raise NotImplementedError(
                "'with_wrap_before_operator' only valid when there are 2 operands")
        return self.with_wrapping_at(1)

    def with_wrap_after_operator(self):
        if self.operands.num_entries() != 2:
            raise NotImplementedError(
                "'with_wrap_after_operator' only valid when there are 2 operands")
        return self.with_wrapping_at(2)

    def with_justification(self, justification):
        return self.with_styles(justification=justification)

    @classmethod
    def _implicitOperator(operation_class):
        if hasattr(operation_class, '_operator_'):
            return operation_class._operator_
        return None

    @classmethod
    def extract_init_arg_value(
            cls,
            arg_name,
            operator_or_operators,
            operand_or_operands):
        '''
        Given a name of one of the arguments of the __init__ method,
        return the corresponding value contained in the 'operands'
        composite expression (i.e., the operands of a constructed operation).

        Except when this is an OperationOverInstances, this method should
        be overridden if you cannot simply pass the operands directly
        into the __init__ method.
        '''
        raise NotImplementedError(
            "'extract_init_arg_value' must be appropriately implemented if __init__ arguments do not fall into a simple 'default' scenario")

    def extract_my_init_arg_value(self, arg_name):
        '''
        Given a name of one of the arguments of the __init__ method,
        return the corresponding value appropriate for reconstructing self.
        The default calls the extract_init_arg_value static method.  Overload
        this when the most proper way to construct the expression is style
        dependent.  Then "remake_arguments" will use this overloaded method.
        "_make" will do it via the static method but will fix the styles
        afterwards.
        '''
        return self.__class__.extract_init_arg_value(
            arg_name, self.operator_or_operators, self.operand_or_operands)

    def _extractMyInitArgs(self):
        '''
        Call the _extract_init_args class method but will set "obj" to "self".
        This will cause extract_my_init_arg_value to be called instead of
        the extract_init_arg_value static method.
        '''
        return self.__class__._extract_init_args(
            self.operator_or_operators, self.operand_or_operands, obj=self)

    @classmethod
    def _extract_init_args(
            cls,
            operator_or_operators,
            operand_or_operands,
            obj=None):
        '''
        For a particular Operation class and given operator(s) and operand(s),
        yield (name, value) pairs to pass into the initialization method
        for creating the operation consistent with the given operator(s) and operand(s).

        First attempt to call 'extract_init_arg_value' (or 'extract_my_init_arg_value' if
        'obj' is provided) for each of the __init__ arguments to determine how
        to generate the appropriate __init__ parameters from the given operators
        and operands.  If that is not implemented, fall back to one of the
        following default scenarios.

        If the particular Operation class has an 'implicit operator' defined
        via an _operator_ attribute and the number of __init__ arguments matches the
        number of operands or it takes only a single *args variable-length argument
        list: construct the Operation by passing each operand individually.

        Otherwise, if there is no 'implicit operator' and __init__ accepts
        only two arguments (no variable-length or keyward arguments): construct
        the Operation by passeng the operation(s) as the first argument
        and operand(s) as the second argument.  If the length of either of
        these is 1, then the single expression is passed rather than a
        composite.

        Otherwise, if there is no 'implicit operator' and __init__ accepts
        one formal  argument and a variable-length argument and no keyword
        arguments, or a number of formal arguments equal to the number of operands
        plus 1 and no variable-length argument and no keyword arguments:
        construct the Operation by passing the operator(s) and
        each operand individually.
        '''
        from proveit._core_.expression.composite.composite import composite_expression
        implicit_operator = cls._implicitOperator()
        matches_implicit_operator = (
            operator_or_operators == implicit_operator)
        if implicit_operator is not None and not matches_implicit_operator:
            raise OperationError("An implicit operator may not be changed")
        operands = composite_expression(operand_or_operands)
        args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, _ = \
            inspect.getfullargspec(cls.__init__)
        args = args[1:]  # skip over the 'self' arg
        if len(args) > 0 and args[-1] == 'styles':
            # NOT TREATING 'styles' FULLY AT THIS TIME; THIS NEEDS WORK.
            args = args[:-1]
            defaults = defaults[:-1]
        if obj is None:
            def extract_init_arg_value_fn(arg): return cls.extract_init_arg_value(
                arg, operator_or_operators, operand_or_operands)
        else:
            extract_init_arg_value_fn = \
                lambda arg: obj.extract_my_init_arg_value(arg)
        try:
            arg_vals = [extract_init_arg_value_fn(arg) for arg in args]
            if varargs is not None:
                arg_vals += extract_init_arg_value_fn(varargs)
            if defaults is None:
                defaults = []
            for k, (arg, val) in enumerate(zip(args, arg_vals)):
                if len(defaults) - len(args) + k < 0:
                    if not isinstance(val, Expression):
                        raise TypeError(
                            "extract_init_arg_val for %s should return an Expression but is returning a %s" %
                            (arg, type(val)))
                    yield val  # no default specified; just supply the value, not the argument name
                else:
                    if val == defaults[len(defaults) - len(args) + k]:
                        continue  # using the default value
                    else:
                        yield (arg, val)  # override the default
            if varkw is not None:
                kw_arg_vals = extract_init_arg_value_fn(varkw)
                for arg, val in kw_arg_vals.items():
                    yield (arg, val)
            if kwonlyargs is not None:
                for kwonlyarg in kwonlyargs:
                    val = extract_init_arg_value_fn(kwonlyarg)
                    if val != kwonlydefaults[kwonlyarg]:
                        yield (kwonlyarg, val)
        except NotImplementedError:
            # and (operation_class.extract_init_arg_value ==
            # Operation.extract_init_arg_value):
            if (varkw is None):
                # try some default scenarios (that do not involve keyword arguments)
                # handle default implicit operator case
                if implicit_operator and (
                    (len(args) == 0 and varargs is not None) or (
                        len(args) == operands.num_entries() and varargs is None)):
                    # yield each operand separately
                    for operand in operands:
                        yield operand
                    return

                # handle default explicit operator(s) case
                if (not implicit_operator) and (varkw is None):
                    if varargs is None and len(args) == 2:
                        # assume one argument for the operator(s) and one
                        # argument for the operand(s)
                        yield operator_or_operators
                        yield operand_or_operands
                        return
                    elif ((varargs is not None and len(args) == 1) or 
                          (len(args) == operands.num_entries() + 1 
                           and varargs is None)):
                        # yield the operator(s) and each operand separately
                        yield operator_or_operators
                        for operand in operands:
                            yield operand
                        return
                raise NotImplementedError(
                    "Must implement 'extract_init_arg_value' for the "
                    "Operation of type %s if it does not fall into "
                    "one of the default cases for 'extract_init_args'"
                    % str(cls))

    @classmethod
    def _make(operation_class, core_info, styles, sub_expressions):
        '''
        Make the appropriate Operation.  core_info should equal ['Operation'].  The first
        of the sub_expressions should be the operator(s) and the second should be the
        operand(s).  This implementation expects the Operation sub-class to have a
        class variable named '_operator_' that defines the Literal operator
        of the class.  It will instantiate the Operation sub-class with just *operands
        and check that the operator is consistent.  Override this method
        if a different behavior is desired.
        '''
        if len(core_info) != 1 or core_info[0] != 'Operation':
            raise ValueError(
                "Expecting Operation core_info to contain exactly one item: 'Operation'")
        if len(sub_expressions) == 0:
            raise ValueError(
                'Expecting at least one sub_expression for an Operation, for the operator')
        operator_or_operators, operand_or_operands = sub_expressions[0], sub_expressions[1]
        args = []
        kw_args = dict()
        for arg in operation_class._extract_init_args(
                operator_or_operators, operand_or_operands):
            if isinstance(arg, Expression):
                args.append(arg)
            else:
                kw, val = arg
                kw_args[kw] = val
        made_operation = operation_class(*args, **kw_args)
        if styles is not None:
            made_operation.with_styles(**styles)
        return made_operation

    def remake_arguments(self):
        '''
        Yield the argument values or (name, value) pairs
        that could be used to recreate the Operation.
        '''
        for arg in self._extractMyInitArgs():
            yield arg

    def remake_with_style_calls(self):
        '''
        In order to reconstruct this Expression to have the same styles,
        what "with..." method calls are most appropriate?  Return a
        tuple of strings with the calls to make.  The default for the
        Operation class is to include appropriate 'with_wrapping_at'
        and 'with_justification' calls.
        '''
        wrap_positions = self.wrap_positions()
        call_strs = []
        if len(wrap_positions) > 0:
            call_strs.append('with_wrapping_at(' + ','.join(str(pos)
                                                            for pos in wrap_positions) + ')')
        justification = self.get_style('justification')
        if justification != 'center':
            call_strs.append('with_justification("' + justification + '")')
        return call_strs

    def string(self, **kwargs):
        # When there is a single operand, we must use the "function"-style
        # formatting.
        if self.get_style('operation') == 'function' or not hasattr(
                self, 'operands'):
            return self._function_formatted('string', **kwargs)
        return self._formatted('string', **kwargs)

    def latex(self, **kwargs):
        # When there is a single operand, we must use the "function"-style
        # formatting.
        if self.get_style('operation') == 'function' or not hasattr(
                self, 'operands'):
            return self._function_formatted('latex', **kwargs)
        return self._formatted('latex', **kwargs)

    def wrap_positions(self):
        '''
        Return a list of wrap positions according to the current style setting.
        '''
        return [int(pos_str) for pos_str in self.get_style(
            'wrap_positions').strip('()').split(' ') if pos_str != '']

    def _function_formatted(self, format_type, **kwargs):
        from proveit._core_.expression.composite.expr_tuple import ExprTuple
        formatted_operator = self.operator.formatted(format_type, fence=True)
        if hasattr(
                self,
                'operand') and not isinstance(
                self.operand,
                ExprTuple):
            return '%s(%s)' % (formatted_operator,
                               self.operand.formatted(format_type, fence=False))
        return '%s(%s)' % (formatted_operator,
                           self.operand_or_operands.formatted(
                               format_type, fence=False, sub_fence=False))

    def _formatted(self, format_type, **kwargs):
        '''
        Format the operation in the form "A * B * C" where '*' is a stand-in for
        the operator that is obtained from self.operator.formatted(format_type).

        '''
        if hasattr(self, 'operator'):
            return Operation._formattedOperation(
                format_type,
                self.operator,
                self.operands,
                wrap_positions=self.wrap_positions(),
                justification=self.get_style('justification'),
                **kwargs)
        else:
            return Operation._formattedOperation(
                format_type,
                self.operators,
                self.operands,
                wrap_positions=self.wrap_positions(),
                justification=self.get_style('justification'),
                **kwargs)

    @staticmethod
    def _formattedOperation(
            format_type,
            operator_or_operators,
            operands,
            wrap_positions,
            justification,
            implicit_first_operator=False,
            **kwargs):
        from proveit import ExprRange, ExprTuple, composite_expression
        if isinstance(
                operator_or_operators,
                Expression) and not isinstance(
                operator_or_operators,
                ExprTuple):
            operator = operator_or_operators
            # Single operator case.
            # Different formatting when there is 0 or 1 element, unless
            # it is an ExprRange.
            if operands.num_entries() < 2:
                if operands.num_entries() == 0 or not isinstance(
                        operands[0], ExprRange):
                    if format_type == 'string':
                        return '[' + operator.string(fence=True) + '](' + operands.string(
                            fence=False, sub_fence=False) + ')'
                    else:
                        return r'\left[' + operator.latex(fence=True) + r'\right]\left(' + operands.latex(
                            fence=False, sub_fence=False) + r'\right)'
                    raise ValueError(
                        "Unexpected format_type: " + str(format_type))
            fence = kwargs.get('fence', False)
            sub_fence = kwargs.get('sub_fence', True)
            do_wrapping = len(wrap_positions) > 0
            formatted_str = ''
            formatted_str += operands.formatted(format_type,
                                                fence=fence,
                                                sub_fence=sub_fence,
                                                operator_or_operators=operator,
                                                wrap_positions=wrap_positions,
                                                justification=justification)
            return formatted_str
        else:
            operators = operator_or_operators
            operands = composite_expression(operands)
            # Multiple operator case.
            # Different formatting when there is 0 or 1 element, unless it is
            # an ExprRange
            if operands.num_entries() < 2:
                if operands.num_entries() == 0 or not isinstance(
                        operands[0], ExprRange):
                    raise OperationError(
                        "No defaut formatting with multiple operators and zero operands")
            fence = kwargs['fence'] if 'fence' in kwargs else False
            sub_fence = kwargs['sub_fence'] if 'sub_fence' in kwargs else True
            do_wrapping = len(wrap_positions) > 0
            formatted_str = ''
            if fence:
                formatted_str = '(' if format_type == 'string' else r'\left('
            if do_wrapping and format_type == 'latex':
                formatted_str += r'\begin{array}{%s} ' % justification[0]
            formatted_str += operands.formatted(format_type,
                                                fence=False,
                                                sub_fence=sub_fence,
                                                operator_or_operators=operators,
                                                implicit_first_operator=implicit_first_operator,
                                                wrap_positions=wrap_positions)
            if do_wrapping and format_type == 'latex':
                formatted_str += r' \end{array}'
            if fence:
                formatted_str += ')' if format_type == 'string' else r'\right)'
            return formatted_str

    def _replaced(self, repl_map, allow_relabeling,
                  assumptions, requirements, equality_repl_requirements):
        '''
        Returns this expression with sub-expressions substituted
        according to the replacement map (repl_map) dictionary.

        When an operater of an Operation is substituted by a Lambda map,
        the operation itself will be substituted with the Lambda map
        applied to the operands.  For example, substituting
        f : (x,y) -> x+y
        on f(a, b) will result in a+b.  When performing operation
        substitution with a range of parameters, the Lambda map
        application will require the number of these parameters
        to equal with the number of corresponding operand elements.
        For example,
        f : (a, b_1, ..., b_n) -> a*b_1 + ... + a*b_n
        n : 3
        applied to f(w, x, y, z) will result in w*x + w*y + w*z provided
        that |(b_1, ..., b_3)| = |(x, y, z)| is proven.
        Assumptions may be needed to prove such requirements.
        Requirements will be appended to the 'requirements' list if one
        is provided.

        There are limitations with respect the Lambda map application involving
        iterated parameters when perfoming operation substitution in order to
        keep derivation rules (i.e., instantiation) simple.  For details,
        see the ExprRange.substituted documentation.
        '''
        from proveit import (Lambda, single_or_composite_expression,
                             composite_expression, ExprTuple, ExprRange)

        if len(repl_map) > 0 and (self in repl_map):
            # The full expression is to be substituted.
            return repl_map[self]

        # Perform substitutions for the operator(s) and operand(s).
        subbed_operator_or_operators = \
            self.operator_or_operators.replaced(repl_map, allow_relabeling,
                                                assumptions, requirements,
                                                equality_repl_requirements)
        subbed_operand_or_operands = \
            self.operand_or_operands.replaced(repl_map, allow_relabeling,
                                              assumptions, requirements,
                                              equality_repl_requirements)
        subbed_operators = composite_expression(subbed_operator_or_operators)

        # Check if the operator is being substituted by a Lambda map in
        # which case we should perform full operation substitution.
        if subbed_operators.num_entries() == 1:
            subbed_operator = subbed_operators[0]
            if isinstance(subbed_operator, Lambda):
                # Substitute the entire operation via a Lambda map
                # application.  For example, f(x, y) -> x + y,
                # or g(a, b_1, ..., b_n) -> a * b_1 + ... + a * b_n.

                if isinstance(subbed_operator.body, ExprRange):
                    raise ImproperReplacement(
                        self, repl_map,
                        "The function %s cannot be defined using this "
                        "lambda, %s, that has an ExprRange for its body; "
                        "that could lead to tuple length contradictions."
                        % (self.operator, subbed_operator))
                if self.operands.num_entries() == 1 and \
                        not isinstance(self.operands[0], ExprRange):
                    # A single operand case (even if that operand
                    # happens to be a tuple).
                    subbed_operands = [subbed_operand_or_operands]
                else:
                    subbed_operands = subbed_operand_or_operands.entries
                return Lambda._apply(
                    subbed_operator.parameters, subbed_operator.body,
                    *subbed_operands, assumptions=assumptions,
                    requirements=requirements,
                    equality_repl_requirements=equality_repl_requirements)

        had_singular_operand = hasattr(self, 'operand')
        if (had_singular_operand and isinstance(subbed_operand_or_operands,
                                                ExprTuple)
                and not isinstance(self.operand_or_operands, ExprTuple)):
            # If a singular operand is replaced with an ExprTuple,
            # we must wrap an extra ExprTuple around it to indicate
            # that it is still a singular operand with the operand
            # as the ExprTuple (rather than expanding to multiple
            # operands).
            subbed_operand_or_operands = ExprTuple(subbed_operand_or_operands)
        else:
            # Possibly collapse multiple operands to a single operand
            # via "do_singular_reduction=True".
            subbed_operand_or_operands = single_or_composite_expression(
                subbed_operand_or_operands, do_singular_reduction=True)

        # Remake the Expression with substituted operator and/or
        # operands
        if subbed_operators.num_entries() == 1:
            # If it is a single operator that is a literal operator of
            # an Operation class defined via an "_operator_" class
            # attribute, then create the Operation of that class.
            operator = subbed_operators[0]
            if operator in Operation.operation_class_of_operator:
                op_class = Operation.operation_class_of_operator[operator]
                if op_class != self.__class__:
                    # Don't transfer the styles; they may not apply in
                    # the same manner in the setting of the new
                    # operation.
                    subbed_sub_exprs = (operator, subbed_operand_or_operands)
                    substituted = op_class._checked_make(
                        ['Operation'], styles=None,
                        sub_expressions=subbed_sub_exprs)
                    return substituted._auto_reduced(
                        assumptions, requirements,
                        equality_repl_requirements)

        subbed_sub_exprs = (subbed_operator_or_operators,
                            subbed_operand_or_operands)
        substituted = self.__class__._checked_make(
            self._core_info, self.get_styles(), subbed_sub_exprs)
        return substituted._auto_reduced(assumptions, requirements,
                                         equality_repl_requirements)


class OperationError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message
