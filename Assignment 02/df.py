import sys
import json
from collections import namedtuple

from form_blocks import form_blocks
import cfg

# A single dataflow analysis consists of these part:
# - forward: True for forward, False for backward.
# - init: An initial value (bottom or top of the latice).
# - merge: Take a list of values and produce a single value.
# - transfer: The transfer function.
Analysis = namedtuple("Analysis", ["forward", "init", "merge", "transfer"])


def union(sets):
    out = set()
    for s in sets:
        out.update(s)
    return out


def df_worklist(blocks, analysis):
    """The worklist algorithm for iterating a data flow analysis to a
    fixed point.
    """
    preds, succs = cfg.edges(blocks)

    # Switch between directions.
    if analysis.forward:
        first_block = list(blocks.keys())[0]  # Entry.
        in_edges = preds
        out_edges = succs
    else:
        first_block = list(blocks.keys())[-1]  # Exit.
        in_edges = succs
        out_edges = preds

    # Initialize.
    in_ = {first_block: analysis.init}
    out = {node: analysis.init for node in blocks}

    # Iterate.
    worklist = list(blocks.keys())
    while worklist:
        node = worklist.pop(0)

        inval = analysis.merge(out[n] for n in in_edges[node])
        in_[node] = inval

        outval = analysis.transfer(blocks[node], inval)

        if outval != out[node]:
            out[node] = outval
            worklist += out_edges[node]

    if analysis.forward:
        return in_, out
    else:
        return out, in_


def fmt(val):
    """Guess a good way to format a data flow value. (Works for sets and
    dicts, at least.)
    """
    if isinstance(val, set):
        if val:
            # Check if set contains tuples
            if val and isinstance(next(iter(val)), tuple):
                first_item = next(iter(val))
                if len(first_item) == 2 and isinstance(first_item[1], str):
                    # Reaching definitions: (var, def_id)
                    return ", ".join("{}:{}".format(v, d) for v, d in sorted(val))
                else:
                    # Available expressions: (op, args) or (call, func, args)
                    return ", ".join(str(expr) for expr in sorted(val))
            else:
                return ", ".join(v for v in sorted(val))
        else:
            return "∅"
    elif isinstance(val, dict):
        if val:
            return ", ".join("{}: {}".format(k, v) for k, v in sorted(val.items()))
        else:
            return "∅"
    else:
        return str(val)


def run_df(bril, analysis):
    for func in bril["functions"]:
        # Form the CFG.
        blocks = cfg.block_map(form_blocks(func["instrs"]))
        cfg.add_terminators(blocks)

        in_, out = df_worklist(blocks, analysis)
        for block in blocks:
            print("{}:".format(block))
            print("  in: ", fmt(in_[block]))
            print("  out:", fmt(out[block]))


def gen(block):
    """Variables that are written in the block."""
    return {i["dest"] for i in block if "dest" in i}


def use(block):
    """Variables that are read before they are written in the block."""
    defined = set()  # Locally defined.
    used = set()
    for i in block:
        used.update(v for v in i.get("args", []) if v not in defined)
        if "dest" in i:
            defined.add(i["dest"])
    return used


def cprop_transfer(block, in_vals):
    out_vals = dict(in_vals)
    for instr in block:
        if "dest" in instr:
            if instr["op"] == "const":
                out_vals[instr["dest"]] = instr["value"]
            else:
                out_vals[instr["dest"]] = "?"
    return out_vals


def cprop_merge(vals_list):
    out_vals = {}
    for vals in vals_list:
        for name, val in vals.items():
            if val == "?":
                out_vals[name] = "?"
            else:
                if name in out_vals:
                    if out_vals[name] != val:
                        out_vals[name] = "?"
                else:
                    out_vals[name] = val
    return out_vals


def rd_transfer(block, in_defs):
    """Transfer function for reaching definitions.
    Kill all previous definitions of variables defined in this block,
    then generate new definitions for variables defined in this block.
    """
    out_defs = set(in_defs)  # Start with input definitions
    
    # Process each instruction in the block
    for i, instr in enumerate(block):
        if "dest" in instr:
            var = instr["dest"]
            
            # Kill all previous definitions of this variable
            out_defs = {(v, def_label) for v, def_label in out_defs if v != var}
            
            # Generate new definition for this variable
            # Use instruction index as a unique identifier within the block
            def_id = f"instr_{i}"
            out_defs.add((var, def_id))
    
    return out_defs


def rd_merge(defs_list):
    """Merge function for reaching definitions.
    Take the union of all reaching definitions from predecessor blocks.
    """
    return union(defs_list)


def get_expressions(block):
    """Extract all expressions computed in a block.
    Returns a set of (op, args) tuples representing expressions.
    """
    expressions = set()
    for instr in block:
        if "op" in instr and "args" in instr and instr["op"] != "const":
            # Create expression tuple: (operation, sorted_arguments)
            # Sort arguments to handle commutative operations consistently
            if instr["op"] in ["add", "mul", "eq", "and", "or"]:  # Commutative ops
                args = tuple(sorted(instr["args"]))
            else:
                args = tuple(instr["args"])
            expressions.add((instr["op"], args))
        elif "op" in instr and instr["op"] == "call" and "funcs" in instr:
            # Handle function calls
            args = tuple(instr.get("args", []))
            expressions.add(("call", instr["funcs"][0], args))
    return expressions


def kill_expressions(expressions, killed_var):
    """Remove all expressions that use the given variable."""
    return {expr for expr in expressions 
            if not uses_variable(expr, killed_var)}


def uses_variable(expr, var):
    """Check if an expression uses a given variable."""
    if len(expr) == 2:  # (op, args)
        op, args = expr
        return var in args
    elif len(expr) == 3:  # (call, func_name, args) 
        op, func_name, args = expr
        return var in args
    return False


def ae_transfer(block, in_exprs):
    """Transfer function for available expressions analysis.
    Kill expressions that use redefined variables, then generate new expressions.
    """
    out_exprs = set(in_exprs)  # Start with input expressions
    
    # Process each instruction in the block
    for instr in block:
        if "dest" in instr:
            # Kill all expressions that use the variable being redefined
            killed_var = instr["dest"]
            out_exprs = kill_expressions(out_exprs, killed_var)
            
            # Generate new expression if this instruction computes one
            if "op" in instr and "args" in instr and instr["op"] != "const":
                if instr["op"] in ["add", "mul", "eq", "and", "or"]:  # Commutative ops
                    args = tuple(sorted(instr["args"]))
                else:
                    args = tuple(instr["args"])
                out_exprs.add((instr["op"], args))
            elif "op" in instr and instr["op"] == "call" and "funcs" in instr:
                # Handle function calls
                args = tuple(instr.get("args", []))
                out_exprs.add(("call", instr["funcs"][0], args))
    
    return out_exprs


def ae_merge(exprs_list):
    """Merge function for available expressions analysis.
    Take the intersection of expressions (must be available on ALL paths).
    """
    # Convert generator to list
    expr_sets = list(exprs_list)
    
    if not expr_sets:
        return set()
    
    # Start with the first set
    result = set(expr_sets[0])
    
    # Intersect with all other sets
    for exprs in expr_sets[1:]:
        result = result.intersection(exprs)
    
    return result


ANALYSES = {
    # A really really basic analysis that just accumulates all the
    # currently-defined variables.
    "defined": Analysis(
        True,
        init=set(),
        merge=union,
        transfer=lambda block, in_: in_.union(gen(block)),
    ),
    # Live variable analysis: the variables that are both defined at a
    # given point and might be read along some path in the future.
    "live": Analysis(
        False,
        init=set(),
        merge=union,
        transfer=lambda block, out: use(block).union(out - gen(block)),
    ),
    # A simple constant propagation pass.
    "cprop": Analysis(
        True,
        init={},
        merge=cprop_merge,
        transfer=cprop_transfer,
    ),
    # Reaching definitions analysis: tracks which definitions of variables
    # can reach each program point.
    "reaching": Analysis(
        True,
        init=set(),
        merge=rd_merge,
        transfer=rd_transfer,
    ),
    # Available expressions analysis: tracks expressions that are computed
    # on all paths to a program point and haven't been invalidated.
    "available": Analysis(
        True,
        init=set(),
        merge=ae_merge,
        transfer=ae_transfer,
    ),
}

if __name__ == "__main__":
    bril = json.load(sys.stdin)
    run_df(bril, ANALYSES[sys.argv[1]])
