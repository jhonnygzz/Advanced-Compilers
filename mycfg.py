import json
import sys



TERMINATORS = 'jmp', 'br', 'ret'

def get_path_lengths(cfg, entry):

    search_dict = {}
    search_dict[entry] = 0
    queue = [entry]

    while queue:
        node = queue.pop(0)
        for succ in cfg[node]:
            if succ not in search_dict:
                search_dict[succ] = search_dict[node] + 1
                queue.append(succ)

    return search_dict

def reverse_postorder(cfg, entry):
    visited = set()
    postorder = []

    def dfs(node):
        if node in visited:
            return
        visited.add(node)
        for succ in cfg.get(node, []):
            dfs(succ)
        postorder.append(node)

    dfs(entry)
    return postorder[::-1]  
 

def find_back_edges(cfg, entry):
    back_edges = []
    visited = set()
    stack = set()

    def dfs(u):
        visited.add(u)
        stack.add(u)
        for v in cfg.get(u, []):
            if v not in visited:
                dfs(v)
            elif v in stack:
                back_edges.append((u, v))
        stack.remove(u)

    dfs(entry)
    return back_edges

def is_reducible(cfg, entry):
    back_edges = find_back_edges(cfg, entry)
    for (u, v) in back_edges:
        visited = set()
        stack = [u]
        while stack:
            node = stack.pop()
            if node == v or node in visited:
                continue
            visited.add(node)
            for succ in cfg.get(node, []):
                stack.append(succ)
        if v not in visited:
            return False
    return True

def form_blocks(body):
    curr_block = []
    for instr in body: 
        if 'op' in instr: 
            curr_block.append(instr)

            if instr['op'] in TERMINATORS:
                yield curr_block
                curr_block = []

        else: 
            if curr_block:
                yield curr_block
            curr_block = [instr] 

    if curr_block:
        yield curr_block

def block_map(blocks):
    out = {}

    for block in blocks:
        if block and 'label' in block[0]:
            name = block[0]['label']
            block = block[1:]
        else:
            name = 'b{}'.format(len(out))

        out[name] = block
    return out

def get_cfg(name2block):

    out = {}
    names = list(name2block.keys())
    for i, (name, block) in enumerate(name2block.items()):
        if not block:
            succ = []
        else:
            last = block[-1]
            op = last.get('op')
            if op in ('jmp', 'br'):
                succ = last.get('labels', [])
            elif op == 'ret':
                succ = []
            else:
                # Only fall through if not a terminator
                if i + 1 < len(names):
                    succ = [names[i + 1]]
                else:
                    succ = []
        out[name] = succ
    return out


def mycfg():
    cfg_complete = None
    prog = json.load(sys.stdin)
    for func in prog['functions']:
        name2block = block_map(form_blocks(func['instrs']))
        cfg = get_cfg(name2block)
        cfg_complete = cfg
        print('digraph {} {{'.format((func['name'])))
        for name in name2block:
            print('   {}'.format(name))
        for name, succs in cfg.items():
            for succ in succs:
                print('   {} -> {}'.format(name, succ))
        print('}')
            
        

    return cfg_complete





if __name__ == "__main__":
    complete_cfg = mycfg()
    path_lengths = get_path_lengths(complete_cfg, 'b0')
    print("Path Lengths from entry 'b0':", path_lengths)
    reverse_post_order_list = reverse_postorder(complete_cfg, 'b0')
    print("Reverse Post Order from entry 'b0':", reverse_post_order_list)
    back_edges_list = find_back_edges(complete_cfg, 'b0')
    print("Back Edges from entry 'b0':", back_edges_list)
    reducible = is_reducible(complete_cfg, 'b0')
    print("Is the CFG reducible from entry 'b0'?:", reducible)