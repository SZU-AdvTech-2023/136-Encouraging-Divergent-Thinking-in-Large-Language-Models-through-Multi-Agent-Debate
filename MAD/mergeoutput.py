import os
import shutil

input_folder1 = "/public24_data/wzy2023/Multi-Agents-Debate/data/CommonMT/output/"
input_folder2 = "/public24_data/wzy2023/Multi-Agents-Debate/data/CommonMT/output4tran/"
output_folder = "/public24_data/wzy2023/Multi-Agents-Debate/output4sql/"

# 创建输出文件夹
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 遍历第一个文件夹中的文件
for filename in os.listdir(input_folder1):
    file_path1 = os.path.join(input_folder1, filename)
    file_path2 = os.path.join(input_folder2, filename)
    output_path = os.path.join(output_folder, filename)
    
    # 如果第二个文件夹中存在相同的文件，则跳过
    if os.path.exists(file_path2):
        continue
    
    # 复制第一个文件夹中的文件到输出文件夹
    shutil.copyfile(file_path1, output_path)

# 遍历第二个文件夹中的文件
for filename in os.listdir(input_folder2):
    file_path1 = os.path.join(input_folder1, filename)
    file_path2 = os.path.join(input_folder2, filename)
    output_path = os.path.join(output_folder, filename)
    
    # 如果输出文件夹中已经存在相同的文件，则跳过
    if os.path.exists(output_path):
        continue
    
    # 复制第二个文件夹中的文件到输出文件夹
    shutil.copyfile(file_path2, output_path)

print("文件夹中的文件已合并到输出文件夹中。")