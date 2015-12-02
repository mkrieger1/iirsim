import shlex, os, numpy
from .core import Const, Add, Multiply, Delay, Filter

def load_config(filename):
    """Read configuration file and return a filter."""
    # parse config file
    if not os.path.isfile(filename):
        raise IOError('File "%s" does not exist' % filename)
    try:
        f = open(filename)
    except IOError:
        raise IOError('Could not open file "%s"' % filename)

    cfg_items = []
    for (i, line) in enumerate(f):
        try:
            # remove all comments and unnecessary whitespace
            normalizer = shlex.shlex(line)
            normalizer.wordchars += '.-'
            normal_line = ' '.join([t for t in normalizer])
            if normal_line:
                # split up normalized line and build dictionary
                cfg_item = {}
                for part in normal_line.split(','):
                    cfg_split = shlex.split(part)
                    key = cfg_split.pop(0)
                    value = cfg_split
                    cfg_item[key] = value
                cfg_items.append(cfg_item)
        except (IndexError, ValueError):
            raise RuntimeError( \
                'Could not parse line %i of file "%s"' % (i, filename))

    # look for global bit settings
    bits_global        = None
    factor_bits_global = None
    norm_bits_global  = None
    for cfg_item in cfg_items:
        if 'bits_global' in cfg_item:
            if bits_global is None:
                [bits_global] = cfg_item.pop('bits_global')
                bits_global = int(bits_global)
            else:
                raise RuntimeError( \
                    'bits_global must not be specified more than once')
        if 'factor_bits_global' in cfg_item:
            if factor_bits_global is None:
                [factor_bits_global] = cfg_item.pop('factor_bits_global')
                factor_bits_global = int(factor_bits_global)
            else:
                raise RuntimeError( \
                    'factor_bits_global must not be specified more than once')
        if 'norm_bits_global' in cfg_item:
            if norm_bits_global is None:
                [norm_bits_global] = cfg_item.pop('norm_bits_global')
                norm_bits_global = int(norm_bits_global)
            else:
                raise RuntimeError( \
                    'norm_bits_global must not be specified more than once')

    # remove empty items from cfg_items, only node definitions should be left
    cfg_items = filter(None, cfg_items)

    # look for filter nodes
    filter_nodes = {}
    adjacency    = {}
    input_node   = None
    output_node  = None
    for cfg_item in cfg_items:
        # mandatory settings
        try:
            [node] = cfg_item['node']
        except KeyError:
            raise RuntimeError('Node type not specified')
        try:
            [name] = cfg_item['name']
        except KeyError:
            raise RuntimeError('Name not specified')
        # optional settings
        if 'bits' in cfg_item:
            [bits] = map(int, cfg_item['bits'])
        else:
            bits = bits_global
        if 'connect' in cfg_item:
            connect = cfg_item['connect']
        else:
            connect = []
        if 'input' in cfg_item:
            if input_node is None:
                input_node = name
            else:
                raise RuntimeError('More than one input node specified')
        if 'output' in cfg_item:
            if output_node is None:
                output_node = name
            else:
                raise RuntimeError('More than one output node specified')

        # make filter node
        if name not in filter_nodes:
            if bits is not None:
                if node == 'Const':
                    filter_nodes[name] = Const(bits)
                elif node == 'Add':
                    filter_nodes[name] = Add(bits)
                elif node == 'Delay':
                    filter_nodes[name] = Delay(bits)
                elif node == 'Multiply':
                    if 'factor_bits' in cfg_item:
                        [factor_bits] = cfg_item['factor_bits']
                        factor_bits = int(factor_bits)
                    else:
                        factor_bits = factor_bits_global
                    if 'norm_bits' in cfg_item:
                        [norm_bits] = cfg_item['norm_bits']
                        norm_bits = int(norm_bits)
                    else:
                        norm_bits = norm_bits_global
                    if (factor_bits is not None and norm_bits is not None):
                        filter_nodes[name] = Multiply(
                                               bits, factor_bits, norm_bits)
                    if 'factor' in cfg_item:
                        [factor] = cfg_item['factor']
                        factor = float(factor)
                        filter_nodes[name].set_factor(factor, norm=True)
                else:
                    raise ValueError('Unknown node type: %s' % node)
            else:
                raise RuntimeError('Number of bits for node "%s" not specified' \
                                   % name)
            adjacency[name] = connect
        else:
            raise RuntimeError('Node "%s" already present' % name)

    # make filter
    if input_node is None:
        raise RuntimeError('No input node specified')
    elif output_node is None:
        raise RuntimeError('No output node specified')
    else:
        return Filter(filter_nodes, adjacency, input_node, output_node)

def save_config(filt, filename):
    for name in filt._nodes.iterkeys():
        print name # TODO

def read_data(filename):
    if not os.path.isfile(filename):
        raise IOError('File "%s" does not exist' % filename)
    try:
        x = numpy.loadtxt(filename)
        if len(x.shape) == 1:
            x = x.reshape(len(x), 1) # make n-by-1 matrix out of vector
    except IOError:
        raise IOError('Could not read data from file "%s"' % filename)
    if not len(x):
        raise IOError('File "%s" contains no data' % filename)
    return x
    

if __name__=='__main__':
    load_config('directForm2.txt')

