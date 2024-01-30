# 输入文件名和输出文件名
input_file = "input.txt"
output_file = "output.txt"

# 打开输入文件和输出文件
with open(input_file, 'r', encoding='utf-8') as input_file, open(output_file, 'w', encoding='utf-8') as output_file:
    # 逐行读取输入文件
    for line in input_file:
        # 去除行尾的换行符
        line = line.strip()

        # 检查行是否以"227"开头
        if line.startswith("227"):
            # 将匹配的行写入输出文件
            output_file.write(line + '\n')

# 输出文件中包含以227开头的行
print(f"已提取并保存以'227'开头的行到{output_file}")