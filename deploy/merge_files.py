# coding:utf-8
import os
from deploy.modulefinder import ModuleFinder

root_dir = os.path.dirname(os.path.dirname(__file__))
root_dir = root_dir.replace('/', os.sep)
file_path = __file__.replace('/', os.sep)

if __name__ == '__main__':
    finder = ModuleFinder(encoding='utf-8', root_path=r'D:\code\MindgoIncrementalFramework')
    target = r'D:\code\MindgoIncrementalFramework\policys\test01.py'
    finder.load_file(target)
    merge_file = """# coding:utf-8
from collections import OrderedDict, Sequence

import pandas as pd
import datetime
import traceback
    """

    for file in reversed(finder.paths):
        with open(file, encoding='utf-8') as f:
            for line in f:
                if line.startswith('import') or ' import ' in line:
                    continue
                merge_file += line
    with open(os.sep.join([root_dir, 'output', 'ot.py']), 'w', encoding='utf-8') as f:
        f.write(merge_file)
