#/public24_data/qth/chatgpt_test/schema_albation/all/input/input.jsonl
"""



inputs = []
with open('/public24_data/qth/bird_chatgpt/origin_schema/schema_all/input/input.jsonl') as f:
  for line in f:
    data = json.loads(line)
    input = data['input'].replace('\n', '\\n') 
    inputs.append(input)

with open('outputs.txt', 'w') as f:
  for input in inputs:
    f.write(input + '\n')

f.close()

"""

with open("config5.txt", "r") as file:
    lines = file.readlines()
    for i, line in enumerate(lines):
        if "API:" in line:
            api_key = line.split("API:")[-1].strip()
            lines[i] = "\"" + api_key + "\",\n"
        else:
            lines[i] = ""

with open("config5.txt", "w") as file:
    file.writelines(lines)