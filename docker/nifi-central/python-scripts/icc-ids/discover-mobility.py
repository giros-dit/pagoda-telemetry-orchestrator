import os
import sys
import json
import datetime
import pytz
from datetime import datetime, timezone

# In the ExecuteStreamCommand processor of Nifi, sys.stdin is the incoming FlowFile
json_input_content = sys.stdin.read()
# Open JSON file with the list of icc-ids
#json_input_file = open("ues.json", "r")
#json_input_content = json_input_file.read()

json_current_file = '/opt/nifi/nifi-current/icc-ids/icc-infos.json'
rewrite_file = False

if os.path.exists(json_current_file) == True and os.path.getsize(json_current_file) != 0:
    #print("File exists!")
    # Returns JSON object as a dictionary
    json_input_data = json.loads(json_input_content)
    icc_input_infos = json_input_data['icc_infos']
    #print(icc_input_infos)

    json_output_file = open(json_current_file, "r")
    json_current_output_content = json_output_file.read()
    json_current_output_data = json.loads(json_current_output_content)
    icc_output_infos = json_current_output_data['icc_infos']
    #print(icc_output_infos)

    icc_ids_input = list(icc_input_infos.keys())
    icc_ids_output = list(icc_output_infos.keys())
    
    #print(icc_ids_input)
    #print(icc_ids_output)

    coincidencias_icc_ids = 0
    if len(icc_ids_input) == len(icc_ids_output):
        #print("mismas logitudes")
        longitudes = len(icc_ids_input)
        for icc_id_input in icc_ids_input:
            for icc_id_output in icc_ids_output:
                if icc_id_input == icc_id_output:
                    coincidencias_icc_ids += 1

        if coincidencias_icc_ids == longitudes:
            #print("mismos icc_ids")
            mismos_aps = 0
            icc_ids = icc_ids_input
            for icc_id in icc_ids:
                if icc_input_infos[icc_id]['access_point_hw_id'] == icc_output_infos[icc_id]['access_point_hw_id']:
                    mismos_aps += 1
            
            if mismos_aps == longitudes:
                #print("mismos aps")
                json_output_filter = ""
            else:
                #print("distintos aps")
                json_input_data = json.loads(json_input_content)
                json_input_data['mobility_detection_time'] = datetime.now(pytz.timezone('Europe/Madrid')).isoformat()
                json_obj = json.dumps(json_input_data, sort_keys=True, indent=2)
                json_output_filter = json_obj
                rewrite_file = True
        else:
            #print("distintos icc_ids")
            json_input_data = json.loads(json_input_content)
            json_input_data['mobility_detection_time'] = datetime.now(pytz.timezone('Europe/Madrid')).isoformat()
            json_obj = json.dumps(json_input_data, sort_keys=True, indent=2)
            json_output_filter = json_obj
            rewrite_file = True
    else:
        #print("distintas logitudes")
        json_input_data = json.loads(json_input_content)
        json_input_data['mobility_detection_time'] = datetime.now(pytz.timezone('Europe/Madrid')).isoformat()
        json_obj = json.dumps(json_input_data, sort_keys=True, indent=2)
        json_output_filter = json_obj
        rewrite_file = True

else:
    #print("File doesn't exist...")
    json_input_data = json.loads(json_input_content)
    json_input_data['mobility_detection_time'] = datetime.now(pytz.timezone('Europe/Madrid')).isoformat()
    json_obj = json.dumps(json_input_data, sort_keys=True, indent=2)
    json_output_filter = json_obj
    rewrite_file = True
    
if rewrite_file == True:
    with open(json_current_file, 'w') as json_output_file:
        json_output_file.write(json_output_filter)

json_output_data = {}
json_output_data['filter'] = json_output_filter
json_output_content = json.dumps(json_output_data, sort_keys=True, indent=2)

# In the ExecuteStreamCommand processor of Nifi, sys.stdout is the outcoming FlowFile
#print("OUPUT", json_output_content)
sys.stdout.write(json_output_content)
