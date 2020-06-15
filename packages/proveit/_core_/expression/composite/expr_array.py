import types
from .composite import Composite, _simplifiedCoord
from .expr_tuple import ExprTuple
from proveit._core_.expression.expr import Expression, MakeNotImplemented
from proveit._core_.proof import ProofFailure
from proveit._core_.defaults import USE_DEFAULTS
from proveit._core_.expression.style_options import StyleOptions


class ExprArray(ExprTuple):
    '''
    An ExprArray is simply an ExprTuple of ExprTuples or ExprRanges.
    The array is broken up into different rows after each ExprTuple
    or ExprRange. Each column MUST contain the same type of expression.
    '''
    def __init__(self, *expressions, styles=None):
        '''
        Initialize an ExprTuple from an iterable over Expression
        objects.
        '''
        from .expr_range import ExprRange
        if styles is None: styles = dict()
        if 'orientation' not in styles:
            styles['orientation'] = 'horizontal'
        if 'justification' not in styles:
            styles['justification'] = 'center'

        ExprTuple.__init__(self, *expressions, styles=styles)

        for entry in self:
            if not isinstance(entry, ExprTuple) and not isinstance(entry, ExprRange):
                raise ValueError("Contents of an ExprArray must be wrapped in either an ExprRange or ExprTuple.")

        # check each column for same expression throughout
        self.checkRange()

    def styleOptions(self):
        options = StyleOptions(self)
        options.addOption('justification',
                          ("if any wrap positions are set, justify to the 'left', "
                           "'center', or 'right'"))
        options.addOption('orientation',
                          ("to be read from left to right then top to bottom ('horizontal') "
                           "or to be read top to bottom then left to right ('vertical')"))
        return options

    def wrapPositions(self):
        '''
        Return a list of wrap positions according to the current style setting.
        Position 'n' is after the nth comma.
        '''
        return [int(pos_str) for pos_str in self.getStyle('wrapPositions').strip('()').split(' ') if pos_str != '']

    def orientation(self, *wrap):
        '''
        Wrap the expression according to the orientation: 'horizontal' or 'vertical'
        '''
        return self.withWrappingAt(*wrap)

    def string(self, **kwargs):
        return self.formatted('string', **kwargs)

    def latex(self, **kwargs):
        return self.formatted('latex', **kwargs)

    def checkRange(self):
        '''
        If there is an ExprRange contained in the array,
        every item in the same column MUST agree in length
        of the ExprRange.  If not, raise an error.
        '''
        from proveit import IndexedVar
        from .expr_range import ExprRange
        pos = []
        m = 0
        k = 0
        for expr in self:
            if isinstance(expr, ExprTuple):
                i = 0
                count = 0
                for entry in expr:
                    if isinstance(entry, ExprRange):
                        if m == 0:
                            placeholder = []
                            placeholder.append(i)
                            placeholder.append(entry.first().subExpr(1))
                            placeholder.append(entry.last().subExpr(1))
                            pos.append(placeholder)
                        else:
                            if len(pos) == 0:
                                raise ValueError('There is an invalid ExprRange in tuple number %s' % str(i))
                            for item in pos:
                                if item[0] == i:
                                    if entry.first().subExpr(1) != item[1]:
                                        raise ValueError('Columns containing ExprRanges '
                                                         'must agree for every row. %s is '
                                                         'not equal to %s.' % (entry.first().subExpr(1), item[1]))
                                    if entry.last().subExpr(1) != item[2]:
                                        raise ValueError('Columns containing ExprRanges '
                                                         'must agree for every row. %s is '
                                                         'not equal to %s.' % (entry.last().subExpr(1), item[2]))
                                    k += 1
                        count += 3
                    else:
                        count += 1
                    i += 1

                if count != self.getRowLength():
                    raise ValueError('One or more rows are a different length.  Please double check your entries.')
            elif isinstance(expr, ExprRange):
                if isinstance(expr.first(), ExprTuple):
                    first = None
                    last = None
                    for entry in expr.first():
                        if isinstance(entry, ExprTuple):
                            raise ValueError('Nested ExprTuples are not supported. Fencing is an '
                                             'extraneous feature for the ExprArray class.')
                        elif isinstance(entry, ExprRange):
                            if first is None:
                                first = entry.first().subExpr(0).subExpr(1)
                            if first != entry.first().subExpr(0).subExpr(1):
                                raise ValueError('Rows containing ExprRanges must agree for every column. %s is '
                                                 'not equal to %s.' % (first, entry.first().subExpr(0).subExpr(1)))
                            if first != entry.last().subExpr(0).subExpr(1):
                                raise ValueError('Rows containing ExprRanges must agree for every column. %s is '
                                                 'not equal to %s.' % (first, entry.last().subExpr(0).subExpr(1)))
                        else:
                            if first is None:
                                first = entry.subExpr(1)
                            if first != entry.subExpr(1):
                                raise ValueError('Rows containing ExprRanges must agree for every column. %s is '
                                                 'not equal to %s.' % (first, entry.subExpr(1)))
                    for entry in expr.last():
                        if isinstance(entry, ExprTuple):
                            raise ValueError('Nested ExprTuples are not supported. Fencing is an '
                                             'extraneous feature for the ExprArray class.')
                        elif isinstance(entry, ExprRange):
                            if last is None:
                                last = entry.first().subExpr(0).subExpr(1)
                            if last != entry.first().subExpr(0).subExpr(1):
                                raise ValueError('Rows containing ExprRanges must agree for every column. %s is '
                                                 'not equal to %s.' % (first, entry.first().subExpr(0).subExpr(1)))
                            if last != entry.last().subExpr(0).subExpr(1):
                                raise ValueError('Rows containing ExprRanges must agree for every column. %s is '
                                                 'not equal to %s.' % (first, entry.last().subExpr(0).subExpr(1)))
                        else:
                            if last is None:
                                last = entry.subExpr(1)
                            if last != entry.subExpr(1):
                                raise ValueError('Rows containing ExprRanges must agree for every column. %s is '
                                                 'not equal to %s.' % (first, entry.subExpr(1)))

            m += 1
        if k != len(pos):
            raise ValueError('The ExprRange in the first tuple is not in the same column '
                             'as the ExprRange in tuple number %s' % str(m))

    def getColHeight(self):
        '''
        Return the height of the first column of the array in an integer form.
        (Horizontal orientation is assumed)
        '''
        from .expr_range import ExprRange
        output = 0
        for expr in self:
            if isinstance(expr, ExprTuple):
                output += 1
            elif isinstance(expr, ExprRange):
                if self.getStyle('parameterization', 'implicit') == 'explicit':
                    output += 5
                else:
                    output += 3
        return output

    def getRowLength(self):
        '''
        Return the length of the first row of the array in an integer form.
        (Horizontal orientation is assumed)
        '''
        from .expr_range import ExprRange
        from proveit import Variable, IndexedVar
        output = 0

        for expr in self:
            if isinstance(expr, ExprRange):
                if isinstance(expr.first(), ExprRange):
                    if self.getStyle('parameterization', 'implicit') == 'explicit':
                        output += 5
                    else:
                        output += 3
                elif isinstance(expr.first(), ExprTuple):
                    for value in expr.first():
                        if isinstance(value, Variable) or isinstance(value, IndexedVar):
                            output += 1
                        elif isinstance(value, ExprTuple):
                            for var in value:
                                if isinstance(var, Variable) or isinstance(var, IndexedVar):
                                    output += 1
                                elif isinstance(value, ExprTuple):
                                    for operand in value:
                                        if isinstance(operand, ExprRange) or isinstance(operand, ExprTuple):
                                            raise ValueError('This expression is nested too many times to get an '
                                                             'accurate row length. Please consolidate your ExprRange')
                                        else:
                                            output += 1
                        elif isinstance(value, ExprRange):
                            if self.getStyle('parameterization', 'implicit') == 'explicit':
                                output += 5
                            else:
                                output += 3
            if isinstance(expr, ExprTuple):
                for value in expr:
                    if isinstance(value, Variable) or isinstance(value, IndexedVar):
                        output += 1
                    if isinstance(value, ExprTuple):
                        for var in value:
                            if isinstance(var, Variable) or isinstance(var, IndexedVar):
                                output += 1
                            elif isinstance(var, ExprTuple):
                                for operand in value:
                                    if isinstance(operand, ExprRange) or isinstance(operand, ExprTuple):
                                        raise ValueError('This expression is nested too many times to get an '
                                                         'accurate row length. Please consolidate your ExprTuple')
                                    else:
                                        output += 1
                    if isinstance(value, ExprRange):
                        if self.getStyle('parameterization', 'implicit') == 'explicit':
                            output += 5
                        else:
                            output += 3
            break
        return output

    def formatted(self, formatType, fence=False, subFence=False, operatorOrOperators=None, implicitFirstOperator=False,
                  wrapPositions=None, justification=None, orientation=None, **kwargs):
        from .expr_range import ExprRange
        default_style = ("explicit" if formatType == 'string' else 'implicit')

        outStr = ''
        if len(self) == 0 and fence:
            # for an empty list, show the parenthesis to show something.
            return '()'

        if justification is None:
            justification = self.getStyle('justification', 'center')
        if orientation is None:
            orientation = self.getStyle('orientation', 'horizontal')

        if fence:
            outStr = '(' if formatType == 'string' else r'\left('

        if orientation == 'horizontal':
            length = self.getRowLength()
        else:
            length = self.getColHeight()
        if formatType == 'latex':
            outStr += r'\begin{array} {%s} ' % (justification[0] * length) + '\n '

        formatted_sub_expressions = []
        # Track whether or not ExprRange operands are using
        # "explicit" parameterization, because the operators must
        # follow suit.
        using_explicit_parameterization = []
        k = 0
        for sub_expr in self:
            if k != 0 and orientation == 'horizontal':
                # wrap before each expression, excluding the first.
                formatted_sub_expressions.append(r' \\' + ' \n ')
            if isinstance(sub_expr, ExprRange):
                # Handle an ExprRange entry; here the "sub-expressions"
                # are really ExprRange "checkpoints" (first, last, as
                # well as the ExprRange body in the middle if using
                # an 'explicit' style for 'parameterization) as well as
                # ellipses between the checkpoints..
                using_explicit_parameterization.append(
                    sub_expr._use_explicit_parameterization(formatType))

                i = 0
                ell = r''
                vell = []
                # ell will be used to store the vertical ellipses
                # for the horizontal orientation while vell will store
                # the horizontal ellipses for the vertical orientation
                for expr in sub_expr._formatted_checkpoints(formatType,
                                                            fence=False, subFence=False,
                                                            operator=operatorOrOperators):
                    print(expr)
                    # if orientation is 'vertical' replace all \vdots with \cdots and vice versa.
                    if i == 0 and isinstance(sub_expr.first(), ExprTuple):
                        # only do this once, right away
                        m = 0
                        for entry in sub_expr.first().entries:
                            if m == 0:
                                # for the first entry, don't include '&' for formatting purposes
                                if isinstance(entry, ExprTuple):
                                    n = 0
                                    for var in entry:
                                        if n != 0:
                                            if orientation == 'horizontal':
                                                formatted_sub_expressions.append('& ' + var.formatted(formatType,
                                                                                                      fence=False))
                                                if self.getStyle('parameterization', default_style) == 'explicit':
                                                    ell += r' & \colon'
                                                else:
                                                    ell += r' & \vdots'
                                            else:
                                                # if the orientation is 'vertical', include the ellipses
                                                if k == 0:
                                                    formatted_sub_expressions.append(var.formatted(formatType,
                                                                                                   fence=False))
                                                    if self.getStyle('parameterization', default_style) == 'explicit':
                                                        vell.append(r'& ..')
                                                    else:
                                                        vell.append(r'& \cdots')
                                                else:
                                                    formatted_sub_expressions.append('& '
                                                                                     + var.formatted(formatType,
                                                                                                     fence=False))
                                                    if self.getStyle('parameterization', default_style) == 'explicit':
                                                        vell.append(r'& ..')
                                                    else:
                                                        vell.append(r'& \cdots')
                                        else:
                                            # for the first entry, don't include '&' for formatting purposes

                                            if orientation == 'horizontal':
                                                formatted_sub_expressions.append(var.formatted(formatType, fence=False))
                                                if self.getStyle('parameterization', default_style) == 'explicit':
                                                    ell += r'\colon'
                                                else:
                                                    ell += r'\vdots'
                                            else:
                                                # if the orientation is 'vertical', include the ellipses
                                                if k == 0:
                                                    formatted_sub_expressions.append(var.formatted(formatType,
                                                                                                   fence=False))
                                                    if self.getStyle('parameterization', default_style) == 'explicit':
                                                        vell.append(r'& ..')
                                                    else:
                                                        vell.append(r'& \cdots')
                                                else:
                                                    formatted_sub_expressions.append('& ' + var.formatted(formatType,
                                                                                                          fence=False))
                                                    if self.getStyle('parameterization', default_style) == 'explicit':
                                                        vell.append(r'& ..')
                                                    else:
                                                        vell.append(r'& \cdots')
                                        n += 1
                                elif isinstance(entry, ExprRange):
                                    # this is first for both orientations so don't include the '&' for either
                                    using_explicit_parameterization.append(
                                        entry._use_explicit_parameterization(formatType))
                                    formatted_sub_expressions.append(entry.first().formatted(formatType, fence=False))
                                    if orientation == 'horizontal':
                                        formatted_sub_expressions.append(r'& \cdots')
                                        formatted_sub_expressions.append('& ' + entry.last().formatted(formatType,
                                                                                                       fence=False))
                                        if self.getStyle('parameterization', default_style) == 'explicit':
                                            ell += r'\colon & & \colon'
                                        else:
                                            ell += r'\vdots & & \vdots'
                                    else:
                                        # we add an '&' after the \vdots because this is a range of a tuple of a range
                                        formatted_sub_expressions.append(r'\vdots')
                                        if self.getStyle('parameterization', default_style) == 'explicit':
                                            vell.append(r'& ..')
                                        else:
                                            vell.append(r'& \cdots')
                                        vell.append('&')
                                        formatted_sub_expressions.append(entry.last().formatted(formatType,
                                                                                                fence=False))
                                        if self.getStyle('parameterization', default_style) == 'explicit':
                                            vell.append(r'& ..')
                                        else:
                                            vell.append(r'& \cdots')
                                else:
                                    if orientation == 'horizontal':
                                        formatted_sub_expressions.append(entry.formatted(formatType,
                                                                                         fence=False))
                                        if self.getStyle('parameterization', default_style) == 'explicit':
                                            ell += r'\colon'
                                        else:
                                            ell += r'\vdots'
                                    else:
                                        # if the orientation is 'vertical', include the ellipses
                                        if k == 0:
                                            formatted_sub_expressions.append(entry.formatted(formatType,
                                                                                             fence=False))
                                            if self.getStyle('parameterization', default_style) == 'explicit':
                                                vell.append(r'& ..')
                                            else:
                                                vell.append(r'& \cdots')
                                        else:
                                            formatted_sub_expressions.append('& '
                                                                             + entry.formatted(formatType,
                                                                                               fence=False))
                                            if self.getStyle('parameterization', default_style) == 'explicit':
                                                vell.append(r'& ..')
                                            else:
                                                vell.append(r'& \cdots')
                            else:
                                if isinstance(entry, ExprTuple):
                                    for var in entry:
                                        if orientation == 'horizontal':
                                            # this is not the first so we add '&'
                                            formatted_sub_expressions.append('& ' + var.formatted(formatType,
                                                                                                  fence=False))
                                            if self.getStyle('parameterization', default_style) == 'explicit':
                                                ell += r' & \colon'
                                            else:
                                                ell += r' & \vdots'
                                        else:
                                            if k == 0:
                                                # this is still technically the first column so we don't include
                                                # the '&' for formatting purposes
                                                formatted_sub_expressions.append(var.formatted(formatType, fence=False))
                                                if self.getStyle('parameterization', default_style) == 'explicit':
                                                    vell.append(r'& ..')
                                                else:
                                                    vell.append(r'& \cdots')
                                            else:
                                                formatted_sub_expressions.append('& ' + var.formatted(formatType,
                                                                                                      fence=False))
                                                if self.getStyle('parameterization', default_style) == 'explicit':
                                                    vell.append(r'& ..')
                                                else:
                                                    vell.append(r'& \cdots')
                                elif isinstance(entry, ExprRange):
                                    using_explicit_parameterization.append(
                                        entry._use_explicit_parameterization(formatType))
                                    if orientation == 'horizontal':
                                        formatted_sub_expressions.append('& ' + entry.first().formatted(formatType,
                                                                                                        fence=False))
                                        formatted_sub_expressions.append(r'& \cdots')
                                        formatted_sub_expressions.append('& ' + entry.last().formatted(formatType,
                                                                                                       fence=False))
                                        if self.getStyle('parameterization', default_style) == 'explicit':
                                            ell += r' & \colon & & \colon'
                                        else:
                                            ell += r' & \vdots & & \vdots'
                                    else:
                                        # this is still technically the first column so we don't include
                                        # the '&' for formatting purposes
                                        formatted_sub_expressions.append(entry.first().formatted(formatType,
                                                                                                 fence=False))
                                        if self.getStyle('parameterization', default_style) == 'explicit':
                                            vell.append(r'& ..')
                                        else:
                                            vell.append(r'& \cdots ')
                                        formatted_sub_expressions.append(r'\vdots')
                                        vell.append('&')
                                        formatted_sub_expressions.append(entry.last().formatted(formatType,
                                                                                                fence=False))
                                        if self.getStyle('parameterization', default_style) == 'explicit':
                                            vell.append(r'& ..')
                                        else:
                                            vell.append(r'& \cdots ')
                                else:
                                    if orientation == 'horizontal':
                                        # this is not the first so we add '&'
                                        formatted_sub_expressions.append('& ' + entry.formatted(formatType,
                                                                                                fence=False))
                                        if self.getStyle('parameterization', default_style) == 'explicit':
                                            ell += r' & \colon'
                                        else:
                                            ell += r' & \vdots'
                                    else:
                                        if k == 0:
                                            # this is still technically the first column so we don't include
                                            # the '&' for formatting purposes
                                            formatted_sub_expressions.append(entry.formatted(formatType, fence=False))
                                            if self.getStyle('parameterization', default_style) == 'explicit':
                                                vell.append(r'& ..')
                                            else:
                                                vell.append(r'& \cdots')
                                        else:
                                            formatted_sub_expressions.append('& ' + entry.formatted(formatType,
                                                                                                    fence=False))
                                            if self.getStyle('parameterization', default_style) == 'explicit':
                                                vell.append(r'& ..')
                                            else:
                                                vell.append(r'& \cdots')
                            m += 1

                    elif (expr == sub_expr.last().formatted(formatType, fence=False)) \
                            and isinstance(sub_expr.last(), ExprTuple):
                        # if orientation is 'horizontal' this is the last row
                        # if orientation is 'vertical' this is the last column
                        m = 0
                        for entry in sub_expr.last().entries:
                            if m == 0:
                                if isinstance(entry, ExprTuple):
                                    n = 0
                                    for var in entry:
                                        if n != 0:
                                            # regardless of orientation add the '&'
                                            formatted_sub_expressions.append('& ' + var.formatted(formatType,
                                                                                                  fence=False))
                                        else:
                                            if orientation == 'horizontal':
                                                # if its the first one, omit '&' for formatting purposes
                                                formatted_sub_expressions.append(var.formatted(formatType, fence=False))
                                            else:
                                                # add the '&' because this is technically the last column
                                                formatted_sub_expressions.append('& ' + var.formatted(formatType,
                                                                                                      fence=False))
                                        n += 1
                                elif isinstance(sub_expr.last().entries[0], ExprRange):
                                    using_explicit_parameterization.append(
                                        entry._use_explicit_parameterization(formatType))
                                    if orientation == 'horizontal':
                                        # this is the first of the last row so we omit the '&'
                                        formatted_sub_expressions.append(entry.first().formatted(formatType,
                                                                                                 fence=False))
                                        formatted_sub_expressions.append(r'& \cdots')
                                        formatted_sub_expressions.append('& ' + entry.last().formatted(formatType,
                                                                                                       fence=False))
                                    else:
                                        # this is the last column so we include all '&'
                                        formatted_sub_expressions.append('& ' + entry.first().formatted(formatType,
                                                                                                        fence=False))
                                        formatted_sub_expressions.append(r'& \vdots')
                                        formatted_sub_expressions.append('& ' + entry.last().formatted(formatType,
                                                                                                       fence=False))
                                else:
                                    if orientation == 'horizontal':
                                        formatted_sub_expressions.append(entry.formatted(formatType,
                                                                                         fence=False))
                                    else:
                                        formatted_sub_expressions.append('& ' + entry.formatted(formatType,
                                                                         fence=False))
                            else:
                                if isinstance(entry, ExprTuple):
                                    for var in entry:
                                        # this is not the first entry for either orientation so we include an '&'
                                        formatted_sub_expressions.append('& ' + var.formatted(formatType, fence=False))

                                elif isinstance(entry, ExprRange):
                                    using_explicit_parameterization.append(
                                        entry._use_explicit_parameterization(formatType))
                                    # this is not the first entry for either orientation so we include an '&'
                                    formatted_sub_expressions.append('& ' + entry.first().formatted(formatType,
                                                                                                    fence=False))
                                    if orientation == 'horizontal':
                                        formatted_sub_expressions.append(r'& \cdots')
                                    else:
                                        formatted_sub_expressions.append(r'& \vdots')
                                    formatted_sub_expressions.append('& ' + entry.last().formatted(formatType,
                                                                                                   fence=False))
                                else:
                                    # this is not the first entry for either orientation so we include an '&'
                                    formatted_sub_expressions.append('& ' + entry.formatted(formatType, fence=False))
                            m += 1
                    elif i == 1 and isinstance(sub_expr.first(), ExprTuple):
                        if self.getStyle('parameterization', default_style) == 'explicit':
                            print('should be explicit')
                            if orientation == 'horizontal':
                                formatted_sub_expressions.append(r' \\ ' + '\n ' + ell + r' \\ ' + '\n ')
                                n = 0
                                for entry in sub_expr.body:
                                    if n == 0:
                                        formatted_sub_expressions.append(entry.formatted(formatType, fence=False))
                                    else:
                                        formatted_sub_expressions.append('& ' + entry.formatted(formatType,
                                                                                                fence=False))
                                    n += 1
                                formatted_sub_expressions.append(r' \\ ' + '\n ' + ell + r' \\ ' + '\n ')
                            else:
                                for entry in vell:
                                    formatted_sub_expressions.append(entry)
                                for entry in sub_expr.body:
                                        formatted_sub_expressions.append('& ' + entry.formatted(formatType,
                                                                                                fence=False))
                                for entry in vell:
                                    formatted_sub_expressions.append(entry)
                        else:
                            if orientation == 'horizontal':
                                formatted_sub_expressions.append(r' \\ ' + '\n ' + ell + r' \\ ' + '\n ')
                            else:
                                for entry in vell:
                                    formatted_sub_expressions.append(entry)
                    elif isinstance(sub_expr.first(), ExprRange):

                        # this is first for both orientations so don't include the '&' for either
                        if i == 0:
                            entry = sub_expr.first()
                            formatted_sub_expressions.append(entry.first().formatted(formatType, fence=False))
                            if orientation == 'horizontal':
                                formatted_sub_expressions.append(r'& \cdots')
                                formatted_sub_expressions.append('& ' + entry.last().formatted(formatType,
                                                                                               fence=False))
                                formatted_sub_expressions.append(r'\\ ' + '\n' + r' \vdots & & \vdots \\ ' + '\n')
                            else:
                                # we add an '&' after the \vdots because this is a range of a tuple of a range
                                formatted_sub_expressions.append(r'\vdots')

                                formatted_sub_expressions.append(entry.last().formatted(formatType,
                                                                                        fence=False))
                                formatted_sub_expressions.append(r'& \cdots')
                                formatted_sub_expressions.append('&')
                                formatted_sub_expressions.append(r'& \cdots')
                        if i == 2:
                            entry = sub_expr.last()
                            formatted_sub_expressions.append(entry.first().formatted(formatType, fence=False))
                            if orientation == 'horizontal':
                                formatted_sub_expressions.append(r'& \cdots')
                                formatted_sub_expressions.append('& ' + entry.last().formatted(formatType,
                                                                                               fence=False))

                            else:
                                formatted_sub_expressions.append(r'\vdots')

                                formatted_sub_expressions.append(entry.last().formatted(formatType,
                                                                                        fence=False))
                    i += 1
            elif isinstance(sub_expr, ExprTuple):
                # always fence nested expression lists
                inc = 0
                for expr in sub_expr:
                    if inc == 0:
                        # for the first instance, we don't include '&' for formatting purposes
                        if isinstance(expr, ExprRange):
                            using_explicit_parameterization.append(
                                expr._use_explicit_parameterization(formatType))
                            if orientation == 'horizontal':
                                formatted_sub_expressions.append(expr.first().formatted(formatType,
                                                                                        fence=False, subFence=False))
                                formatted_sub_expressions.append(r'& \cdots')
                                formatted_sub_expressions.append('& ' + expr.last().formatted(formatType,
                                                                                              fence=False,
                                                                                              subFence=False))
                            else:
                                if k == 0:
                                    # this is the first column so we don't include '&'
                                    formatted_sub_expressions.append(expr.first().formatted(formatType,
                                                                                            fence=False,
                                                                                            subFence=False))
                                    formatted_sub_expressions.append(r'\vdots')
                                    formatted_sub_expressions.append(expr.last().formatted(formatType,
                                                                                           fence=False,
                                                                                           subFence=False))
                                else:
                                    formatted_sub_expressions.append('& ' + expr.first().formatted(formatType,
                                                                                                   fence=False,
                                                                                                   subFence=False))
                                    formatted_sub_expressions.append(r'& \vdots')
                                    formatted_sub_expressions.append('& ' + expr.last().formatted(formatType,
                                                                                                  fence=False,
                                                                                                  subFence=False))
                        else:
                            if orientation == 'horizontal':
                                # this is the first item in the first row so we do not include the '&'
                                formatted_sub_expressions.append(expr.formatted(formatType,
                                                                                fence=False, subFence=False))
                            else:
                                if k == 0:
                                    # this is still the first column
                                    formatted_sub_expressions.append(expr.formatted(formatType,
                                                                                    fence=False, subFence=False))
                                else:
                                    # this is not the first column
                                    formatted_sub_expressions.append('& ' + expr.formatted(formatType,
                                                                                           fence=False,
                                                                                           subFence=False))
                    else:
                        if isinstance(expr, ExprRange):
                            using_explicit_parameterization.append(
                                expr._use_explicit_parameterization(formatType))
                            if orientation == 'horizontal':
                                # for this orientation this is not the first so we add '&'
                                formatted_sub_expressions.append('& ' + expr.first().formatted(formatType,
                                                                                               fence=False,
                                                                                               subFence=False))
                                formatted_sub_expressions.append(r'& \cdots')
                                formatted_sub_expressions.append('& ' + expr.last().formatted(formatType,
                                                                                              fence=False,
                                                                                              subFence=False))
                            else:
                                if k == 0:
                                    # this is still the first column so we don't add '&'
                                    formatted_sub_expressions.append(expr.first().formatted(formatType,
                                                                                            fence=False,
                                                                                            subFence=False))
                                    formatted_sub_expressions.append(r'\vdots')
                                    formatted_sub_expressions.append(expr.last().formatted(formatType,
                                                                                           fence=False,
                                                                                           subFence=False))
                                else:
                                    formatted_sub_expressions.append('& ' + expr.first().formatted(formatType,
                                                                                                   fence=False,
                                                                                                   subFence=False))
                                    formatted_sub_expressions.append(r'& \vdots')
                                    formatted_sub_expressions.append('& ' + expr.last().formatted(formatType,
                                                                                                  fence=False,
                                                                                                  subFence=False))

                        else:
                            if orientation == 'horizontal':
                                # this is following along the row so we include '&'
                                formatted_sub_expressions.append('& ' + expr.formatted(formatType,
                                                                                       fence=False, subFence=False))
                            else:
                                if k == 0:
                                    # this is the first column so we don't include '&'
                                    formatted_sub_expressions.append(expr.formatted(formatType,
                                                                                    fence=False, subFence=False))
                                else:
                                    # this is not the first column so we do include '&'
                                    formatted_sub_expressions.append('& ' + expr.formatted(formatType,
                                                                                           fence=False, subFence=False))
                    inc += 1
            else:
                raise ValueError("Expressions must be wrapped in either an ExprTuple or ExprRange")
            k += 1

        print(formatted_sub_expressions)
        if orientation == "vertical":
            # up until now, the formatted_sub_expression is still
            # in the order of the horizontal orientation regardless of orientation type
            k = 1
            vert = []
            m = self.getColHeight()
            while k <= self.getRowLength():
                i = 1
                j = k
                for var in formatted_sub_expressions:
                    if i == j:
                        vert.append(var)
                        m -= 1
                        if m == 0:
                            vert.append(r' \\' + ' \n ')
                            m = self.getColHeight()
                        j += self.getRowLength()
                    i += 1
                k += 1
            formatted_sub_expressions = vert

        if operatorOrOperators is None:
            operatorOrOperators = ','
        elif isinstance(operatorOrOperators, Expression) and not isinstance(operatorOrOperators, ExprTuple):
            operatorOrOperators = operatorOrOperators.formatted(formatType, fence=False)
        if isinstance(operatorOrOperators, str):
            # single operator
            formatted_operator = operatorOrOperators
            if operatorOrOperators == ',':
                # e.g.: a, b, c, d
                outStr += (' ').join(formatted_sub_expressions)
            else:
                # e.g.: a + b + c + d
                outStr += (' '+formatted_operator+' ').join(formatted_sub_expressions)
        else:
            # assume all different operators
            formatted_operators = []
            for operator in operatorOrOperators:
                if isinstance(operator, ExprRange):
                    # Handle an ExprRange entry; here the "operators"
                    # are really ExprRange "checkpoints" (first, last,
                    # as well as the ExprRange body in the middle if
                    # using an 'explicit' style for 'parameterization').
                    # For the 'ellipses', we will just use a
                    # placeholder.
                    be_explicit = using_explicit_parameterization.pop(0)
                    formatted_operators += operator._formatted_checkpoints(
                        formatType, fence=False, subFence=False, ellipses='',
                        use_explicit_parameterization=be_explicit)
                else:
                    formatted_operators.append(operator.formatted(formatType, fence=False, subFence=False))
            if len(formatted_sub_expressions) == len(formatted_operators):
                # operator preceeds each operand
                if implicitFirstOperator:
                    outStr = formatted_sub_expressions[0]  # first operator is implicit
                else:
                    outStr = formatted_operators[0] + formatted_sub_expressions[0]  # no space after first operator
                outStr += ' '  # space before next operator
                outStr += ' '.join(
                    formatted_operator + ' ' + formatted_operand for formatted_operator, formatted_operand in
                    zip(formatted_operators[1:], formatted_sub_expressions[1:]))
            elif len(formatted_sub_expressions) == len(formatted_operators) + 1:
                # operator between each operand
                outStr = ' '.join(
                    formatted_operand + ' ' + formatted_operator for formatted_operand, formatted_operator in
                    zip(formatted_sub_expressions, formatted_operators))
                outStr += ' ' + formatted_sub_expressions[-1]
            elif len(formatted_sub_expressions) != len(formatted_operators):
                raise ValueError(
                    "May only perform ExprTuple formatting if the number of operators is equal to the number "
                    "of operands(precedes each operand) or one less (between each operand); "
                    "also, operator ranges must be in correspondence with operand ranges.")

        if formatType == 'latex':
            outStr += r' \end{array}' + ' \n'
        if fence:
            outStr += ')' if formatType == 'string' else r'\right)'
        print(using_explicit_parameterization)
        return outStr



