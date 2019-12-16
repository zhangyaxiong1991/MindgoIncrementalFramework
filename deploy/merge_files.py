# coding:utf-8
import os
from deploy.modulefinder import ModuleFinder
from deploy.distribute.map import Mindgo


cookie = 'MDrVxdHH0Ns5OjpOb25lOjUwMDo0NzUzMzc4OTY6NywxMTExMTExMTExMSw0MDs0NCwxMSw0MDs2LDEsNDA7NSwxLDQwOzEsMSw0MDsyLDEsNDA7MywxLDQwOzUsMSw0MDs4LDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAxLDQwOjo6OjQ2NTMzNzg5NjoxNTc2NDIyNTA2Ojo6MTUzOTc2Mjc4MDo4NjQwMDowOjFiNDU5NGQzZmUwZWQ4ZGU0MjY3MmY4YmMxMDQ1OGMwNTpkZWZhdWx0XzM6MQ%3D%3D'
policys = ['5d5967a00aff7400b41dc8f7',
           '5d7bb95c59553e00b45a7c2f',
           '5d2c916135a06500b58425cb',
           '5d58376e2262ff00b5e9aed1',
           '5c0f6e7e596628000af217d8',
           '5cca9837e9f08c000a8911a8',
           '5c0f6eafa1d595000c836558',
           '5df7888f50df2400b4c1314b',
           '5df789e050df2400b4c1314f',
           '5df788975b623d00b407260c',
           '5df7889d5b623d00b407260d',
           '5df788a3fd1b1e00b4001cbd',
           '5df788aead5b9a00b3b9394e',
           '5df788e35b623d00b407260e',
           '5df788ec5b623d00b407260f',
           '5df788f49a708500b320f95a',
           '5df788fdad5b9a00b3b9394f',
           '5df7890350df2400b4c1314e',
           '5df7890936023300b4b10bb6',
           '5df78912fd1b1e00b4001cbe']
root_dir = os.path.dirname(os.path.dirname(__file__))
root_dir = root_dir.replace('/', os.sep)
file_path = __file__.replace('/', os.sep)

if __name__ == '__main__':
    finder = ModuleFinder(encoding='utf-8', root_path=r'D:\code\MindgoIncrementalFramework')
    target = r'D:\code\MindgoIncrementalFramework\policys\test01.py'
    finder.load_file(target)
    merge_file = """# coding:utf-8
import functools
import copy
import datetime
import traceback
from collections import OrderedDict, Sequence, Iterable

import pandas as pd
    """

    for file in reversed(finder.paths):
        with open(file, encoding='utf-8') as f:
            for line in f:
                if line.startswith('import') or ' import ' in line:
                    continue
                merge_file += line
    with open(os.sep.join([root_dir, 'output', 'ot.py']), 'w', encoding='utf-8') as f:
        f.write(merge_file)

    map_tool = Mindgo(policys, cookie, '2015-05-26', '2016-08-01')
    map_tool.distribute(4000, merge_file)
