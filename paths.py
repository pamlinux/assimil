fn = "application_data_paths.yaml"

import yaml

with open(fn) as f:
    data_paths = yaml.load(f, Loader=yaml.SafeLoader)
print(data_paths)

def get_path(name):
    return data_paths[name]
