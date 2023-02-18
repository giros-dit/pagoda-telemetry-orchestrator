import sys
import json
import hashlib

# Open JSON file with the list of icc-ids
json_file = open("icc-ids.json", "r")
json_content = json_file.read()

# Returns JSON object as a dictionary
json_input_data = json.loads(json_content)
json_obj = json.dumps(json_input_data, sort_keys=True, indent=2)

# MD5 Hash of the dictionary
encoded_icc_ids = hashlib.md5(json_obj.encode("utf-8")).hexdigest()

# In the ExecuteStreamCommand processor of Nifi, sys.stdout is the outcoming FlowFile
json_output_data = {}
json_output_data['encoded_icc-ids'] = encoded_icc_ids
json_enconded_icc_ids = json.dumps(json_output_data, sort_keys=True, indent=2)
sys.stdout.write(json_enconded_icc_ids)
