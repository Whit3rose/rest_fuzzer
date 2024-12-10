import json
import subprocess
import argparse
import re
import requests
import time

# rest fuzzer
# write default json payload to file, then surround the value with "FUZZ" (see payload.json for an example)

# use radamsa to change a value
def radamsa_change_value(value):
    ps = subprocess.Popen(('echo', value), stdout=subprocess.PIPE)
    output = subprocess.check_output(('radamsa'), stdin=ps.stdout)
    ps.wait()
    return output

def change_value(value):
    # only return value if it is utf-8
    while True:
        output = radamsa_change_value(value)
        try:
            output_string = output.decode("utf-8")
            break
        except:
            continue
    
    return output_string.replace("\n", "")

# parse the json file and check what values to manipulate
def change_values_that_have_to_be_fuzzed(payload):
    for key in  payload.keys():
        value = payload.get(key)
        # TODO handle lists
        if isinstance(value, dict):
            change_values_that_have_to_be_fuzzed(value)
        value = str(value)
        # regex to return the indizes of the beginning of the FUZZ keyword
        indexes_of_fuzz_indicators_in_value = [m.start() for m in re.finditer('FUZZ', value)]
        while len(indexes_of_fuzz_indicators_in_value) > 1:
            # get beginning and end of the string that has to be changes
            beginning_of_string_to_be_changed = indexes_of_fuzz_indicators_in_value[0] + 4
            end_of_string_to_be_changed = indexes_of_fuzz_indicators_in_value[1]
            value_to_be_changed = value[beginning_of_string_to_be_changed:end_of_string_to_be_changed]
            changed_value = change_value(value_to_be_changed)
            value = value.replace(f"FUZZ{value_to_be_changed}FUZZ", changed_value)
            indexes_of_fuzz_indicators_in_value = [m.start() for m in re.finditer('FUZZ', value)]
        payload[key] = value

    


parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file_payload", help="file that holds the json payload")
parser.add_argument("-ip", "--ip_address", help="ip address of the host you want to fuzz")
parser.add_argument("-p", "--port", help="port number of the server you want to fuzz")
args = parser.parse_args()

# let's open the file with the json payload and read it's contents
try:
    with open(args.file_payload, 'r') as payload_file:
        payload = json.load(payload_file)
except:
    print("Given Payload File does not exist or cannot be opened. It might also not be valid json?")


# handle http requests
while True:
    change_values_that_have_to_be_fuzzed(payload)
    response = requests.post(f"http://{args.ip_address}:{args.port}", json=payload)
    print(response.status_code)
    time.sleep(0.5)
