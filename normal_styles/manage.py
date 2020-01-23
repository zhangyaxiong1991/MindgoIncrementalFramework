# -*- coding: utf-8 -*- 
# @Time : 2020/1/10 0010 下午 10:53 
# @Author : Maton Zhang 
# @Site :  
# @File : manage.py 
import yaml
import json
from policys.templates import normal_style_policy

from deploy.merge_files import MergeFiles


class PolicyManager:
    @staticmethod
    def get_policy_instances(policy):
        import_items = []
        instance_def_items = []
        assert_items = []
        grade_items = []
        group_style_names = []
        for key, items in policy.items():
            if key == 'configs':
                execute_date = items['execute_date']
                continue

            if key == 'asserts':
                for assert_name, assert_str in items.items():
                    assert_items.append('    if not {}: result_data["assert_error"] += "{} assert not pass"'.format(assert_str.strip().replace('$', 'result_data.'), assert_name))
                continue

            if key == 'grades':
                for grade_name, grade_str in items.items():
                    grade_items.append('    grade += ({})'.format(grade_str.strip().replace('$', 'result_data.')))
                continue

            if key == 'groups':
                for type_name in items:
                    group_style_names.append(type_name)

            for style_name, style in items.items():
                print(style_name)
                style['args']['name'] = style_name
                type_path = [i.strip() for i in style['type'].strip().split('.')]
                import_items.append('.'.join((['from normal_styles'] + type_path[:-1])) + ' import ' + type_path[-1])
                instance_def_items.append('{}(**json.loads(\'{}\'))'.format(type_path[-1], json.dumps(style['args'])))
        import_items = '\n'.join(import_items)
        instance_def_items = ','.join(instance_def_items)
        assert_items = '\n'.join(assert_items)
        grade_items = '\n'.join(grade_items)
        return normal_style_policy.format(instance_items=instance_def_items, execute_date=execute_date, import_items=import_items, dict_item="{}", assert_items=assert_items, grade_items=grade_items, group_style_names=str(json.dumps(group_style_names)))


if __name__ == '__main__':
    with open('policy03.yaml', 'r', encoding='utf-8') as f:
        policy = yaml.load(f.read())
        policy_content = PolicyManager.get_policy_instances(policy)
        print(policy_content)

    with open(r'..\policys\test001.py', 'w', encoding='utf-8') as f:
        f.write(policy_content)

    MergeFiles.merge_files(r'..\policys\test001.py', r'..\output\ot.py')
