import sys
import json
import hashlib

# In the ExecuteStreamCommand processor of Nifi, sys.stdin is the incoming FlowFile
json_input_content = sys.stdin.read()

# Returns JSON object as a dictionary
json_input_data = json.loads(json_input_content)

icc_ids = json_input_data["icc_id"]

icc_ids_unicos = []

for icc_id in icc_ids:
    if icc_id in icc_ids_unicos:
        continue
    else:
        icc_ids_unicos.append(icc_id)

json_output_data = {}
json_output_data['icc_id'] = icc_ids_unicos
json_output_content = json.dumps(json_output_data, sort_keys=True, indent=2)

# In the ExecuteStreamCommand processor of Nifi, sys.stdout is the outcoming FlowFile
sys.stdout.write(json_output_content)
