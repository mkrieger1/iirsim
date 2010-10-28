import shlex

valid_node_types = ['Const', 'Add', 'Multiply', 'Delay']

def readconfig(filename):
    cfg_items = []
    with open(filename) as f:
        for line in f:
            # remove all comments and unnecessary whitespace
            normalizer = shlex.shlex(line)
            normal_line = ' '.join([t for t in normalizer])
            if normal_line:
                # split up normalized line and build dictionary
                cfg_dict = {}
                for part in normal_line.split(','):
                    cfg_item = shlex.split(part)
                    key = cfg_item.pop(0)
                    value = cfg_item
                    cfg_dict[key] = value
                print cfg_dict
                cfg_items.append(cfg_dict)

if __name__=='__main__':
    readconfig('directForm2.txt')

