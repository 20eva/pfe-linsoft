import os

total = 0
layer_counts = {'tf': 0, 'yml': 0}

for root, dirs, files in os.walk('real_data'):
    if '.git' in root:
        continue
    tf  = [f for f in files if f.endswith('.tf')]
    yml = [f for f in files if f.endswith(('.yml', '.yaml'))]
    if tf or yml:
        print(f"{root}: {len(tf)} .tf  |  {len(yml)} .yml")
    layer_counts['tf']  += len(tf)
    layer_counts['yml'] += len(yml)
    total += len(tf) + len(yml)

print(f"\n{'─'*40}")
print(f"Terraform files : {layer_counts['tf']}")
print(f"YAML files      : {layer_counts['yml']}")
print(f"TOTAL           : {total}")