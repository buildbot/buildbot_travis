import ast


def safe_eval(expr, variables):
    """
    Safely evaluate an expression node or a string containing a Python
    expression.  The string or node provided may only consist of the following
    Python literal structures: strings, numbers, tuples, lists, dicts, booleans,
    and None. safe operators are allowed (and, or, ==, !=, not, +, -, ^, %, in, is)
    """
    _safe_names = {'None': None, 'True': True, 'False': False}
    _safe_nodes = [
        'Add', 'And', 'BinOp', 'BitAnd', 'BitOr', 'BitXor', 'BoolOp',
        'Compare', 'Dict', 'Eq', 'Expr', 'Expression', 'For',
        'Gt', 'GtE', 'Is', 'In', 'IsNot', 'LShift', 'List',
        'Load', 'Lt', 'LtE', 'Mod', 'Name', 'Not', 'NotEq', 'NotIn',
        'Num', 'Or', 'RShift', 'Set', 'Slice', 'Str', 'Sub',
        'Tuple', 'UAdd', 'USub', 'UnaryOp', 'boolop', 'cmpop',
        'expr', 'expr_context', 'operator', 'slice', 'unaryop']
    node = ast.parse(expr, mode='eval')
    for subnode in ast.walk(node):
        subnode_name = type(subnode).__name__
        if isinstance(subnode, ast.Name):
            if subnode.id not in _safe_names and subnode.id not in variables:
                raise ValueError("Unsafe expression {}. contains {}".format(expr, subnode.id))
        if subnode_name not in _safe_nodes:
            raise ValueError("Unsafe expression {}. contains {}".format(expr, subnode_name))

    return eval(expr, variables)
