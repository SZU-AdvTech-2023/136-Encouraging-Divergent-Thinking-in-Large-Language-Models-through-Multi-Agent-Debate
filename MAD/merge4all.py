#/public24_data/qth/chatgpt_test/schema_albation/all/input/input.jsonl
import os
import json

#data_folder = "/public24_data/wzy2023/Multi-Agents-Debate/output4sql/"
#/public24_data/wzy2023/Multi-Agents-Debate/data/SQL/output1
data_folder = "/public14_data/wzy2023/Multi-Agents-Debate/data/SQL/output3/"
output_file = "extracted_data_3.jsonl"

start_id = 0
end_id = 1533

# 遍历指定范围内的id
extracted_data = []
for id in range(start_id, end_id+1):
    file_path = os.path.join(data_folder, f"{id}.json")
    
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            json_data = json.load(file)
            
        debate_query = json_data.get("debate_SQL_query")
        if debate_query:
            extracted_data.append({str(id): debate_query})
    else:
        extracted_data.append({f"{id}": None})

# 将提取的数据保存到JSONL文件中
with open(output_file, "w") as file:
    for item in extracted_data:
        file.write(json.dumps(item) + "\n")

print("提取数据已保存到文件中。")



"""to merge
在指定文件夹/public24_data/wzy2023/Multi-Agents-Debate/data/CommonMT/output/下将{id}.json文件中(id = 0 : 1533)的
"debate_SQL_query": "SELECT MAX(`Percent (%) Eligible Free (K-12)`) AS Highest_Eligible_Free_Rate_K12\nFROM frpm\nJOIN schools ON frpm.CDSCode = schools.CDSCode\nWHERE schools.County = 'Alameda County'"
提取成
{"0": "MAX(`Percent (%) Eligible Free (K-12)`)\nFROM frpm\nJOIN schools ON frpm.CDSCode = schools.CDSCode\nWHERE schools.County = 'Alameda County'"}
这个格式并且放在一个jsonl文件里面
若不存在{id}.json则输出
{"id": null}
"""


"""to merge
将文件夹/public24_data/wzy2023/Multi-Agents-Debate/data/CommonMT/output/与/public24_data/wzy2023/Multi-Agents-Debate/data/CommonMT/output2/中的{id}.json文件合并在一个文件夹中,若有相同的{id}.json则保留/public24_data/wzy2023/Multi-Agents-Debate/data/CommonMT/output/中的
"""