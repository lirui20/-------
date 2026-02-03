# 文件批量重命名工具 - 打包说明

## 打包为 EXE 文件

### 方法一：使用批处理文件（推荐）

1. 双击运行 `build_exe.bat` 文件
2. 等待打包完成
3. 生成的 exe 文件位于 `dist` 文件夹中

### 方法二：手动执行命令

1. 确保已安装 PyInstaller：
   ```bash
   pip install pyinstaller
   ```

2. 执行打包命令：
   ```bash
   pyinstaller --clean folder_renamer.spec
   ```

3. 生成的 exe 文件位于 `dist` 文件夹中

### 打包配置说明

- 使用了 spec 文件进行优化配置
- 排除了不必要的库（numpy, pandas, matplotlib等）
- 生成的 exe 文件是单文件模式，方便分发
- 不显示控制台窗口（GUI应用）

## 使用说明

运行 `folder_renamer.exe` 即可使用文件批量重命名工具。

支持的功能：
- 添加前缀/后缀
- 查找替换
- 序号重命名
- 正则替换
- 大小写转换
- 删除字符
- 文件筛选
- 撤销操作
- 导出日志
