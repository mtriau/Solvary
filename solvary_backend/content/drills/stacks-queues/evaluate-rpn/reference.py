import operator

OPS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": lambda a, b: int(a / b),  # truncate toward zero, unlike //
}


def evaluate_rpn(tokens: list[str]) -> int:
    stack: list[int] = []
    for tok in tokens:
        if tok in OPS:
            b, a = stack.pop(), stack.pop()
            stack.append(OPS[tok](a, b))
        else:
            stack.append(int(tok))
    return stack.pop()
