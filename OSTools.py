import os

def get_file_path() -> str:
    """获取当前位置以及此目录下的所有文件名"""
    current_dir = os.getcwd()
    try:
        items = os.listdir(current_dir)
        # 区分文件和目录
        files = []
        dirs = []
        for item in items:
            full_path = os.path.join(current_dir, item)
            if os.path.isfile(full_path):
                files.append(item)
            elif os.path.isdir(full_path):
                dirs.append(item)
        
        result = f"当前目录: {current_dir}\n"
        if files:
            result += f"\n文件 ({len(files)}个):\n" + "\n".join(files)
        if dirs:
            result += f"\n\n目录 ({len(dirs)}个):\n" + "\n".join(dirs)
        
        return result
    except Exception as e:
        return f"Error: {str(e)}"

def read_file(path: str) -> str:
    """读取指定路径文件的内容"""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "Error: File not found."


def write_file(path: str, content: str) -> str:
    """将内容写入指定路径的文件"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Successfully wrote to {path}"

if __name__ == "__main__":
    print(get_file_path())