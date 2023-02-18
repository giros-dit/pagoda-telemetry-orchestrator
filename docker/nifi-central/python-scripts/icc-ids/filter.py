import sys
import json
import hashlib

# In the ExecuteStreamCommand processor of Nifi, sys.stdin is the incoming FlowFile
json_input_content = sys.stdin.read()
#json_file = open("icc-ids-fail.json", "r")
#json_input_content = json_file.read()

# Returns JSON object as a dictionary
json_input_data = json.loads(json_input_content)

subsc = json_input_data["subsc"]

if len(subsc) == 0:
    json_output_filter = ""
else:
    json_output_filter = json_input_content

json_output_data = {}
json_output_data['filter'] = json_output_filter
json_output_content = json.dumps(json_output_data, sort_keys=True, indent=2)
# In the ExecuteStreamCommand processor of Nifi, sys.stdout is the outcoming FlowFile
sys.stdout.write(json_output_content)
