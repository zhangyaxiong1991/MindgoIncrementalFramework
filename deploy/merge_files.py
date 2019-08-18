# coding:utf-8
import os
import sys
import locale
from modulefinder import ModuleFinder

root_dir = os.path.dirname(os.path.dirname(__file__))
root_dir = root_dir.replace('/', os.sep)
file_path = __file__.replace('/', os.sep)

if __name__ == '__main__':
    finder = ModuleFinder(encoding='utf-8')
    target = r'D:\code\MindgoIncrementalFramework\policys\test01.py'
    finder.run_script(target)

    file_list = []
    keys = finder.modules.keys()
    keys = reversed(keys)
    for key in keys:
        m = finder.modules[key]
        if m.__path__:
            print("P", end=' ')
        else:
            print("m", end=' ')
        print("%-25s" % key, m.__file__ or "")

    keys = finder.modules.keys()
    for key in keys:
        m = finder.modules[key]
        if m.__file__ is None:
            continue
        if m.__file__ == file_path:
            continue
        if not m.__file__.startswith(root_dir):
            continue
        if m.__file__ == target:
            continue
        print(key)
        file_list.append(m.__file__)
    file_list.append(target)

    merge_file = ''
    for file in file_list:
        with open(file, encoding='utf-8') as f:
            for line in f:
                if line.startswith('import') or ' import ' in line:
                    continue
                merge_file += line
    with open(os.sep.join([root_dir, 'output', 'ot.py']), 'w', encoding='utf-8') as f:
        f.write(merge_file)
