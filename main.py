import PySimpleGUI as sg
import os
import base64
import subprocess
import threading
from pdf_reader import read1pdf, display_pdf, set_pdf_context, reset_pdf_context

# 定义布局
layout = [
    [sg.Text('选择文件:'), sg.InputText(key='-FILEPATH-'), sg.FileBrowse(button_text='选择文件')],
    [
        sg.Button('打包', key='-PACK-'),
        sg.Button('重置', key='-RESET-'),
        sg.Button('测试', key='-TEST-'),
        sg.Button('退出', key='-EXIT-')
    ],
    [sg.Multiline(size=(80, 15), key='-OUTPUT-', autoscroll=True, disabled=True)]
]

# 创建窗口
window = sg.Window('PDF阅后即焚生成器', layout)

def log_output(window, message):
    """在输出框中添加日志信息"""
    current_output = window['-OUTPUT-'].get()
    new_output = current_output + message + '\n'
    window['-OUTPUT-'].update(new_output)

def validate_file(selected_file_path):
    """验证文件是否存在、是否为PDF文件以及文件大小是否合适"""
    if not os.path.exists(selected_file_path):
        log_output(window, f"文件 {selected_file_path} 不存在")
        return False
    if not selected_file_path.lower().endswith('.pdf'):
        log_output(window, f"文件 {selected_file_path} 不是 PDF 文件")
        return False
    file_size = os.path.getsize(selected_file_path)
    if file_size == 0:
        log_output(window, f"文件 {selected_file_path} 为空")
        return False
    if file_size > 64 * 1024 * 1024:
        log_output(window, f"文件 {selected_file_path} 大于 64MB")
        return False
    return True

def encode_pdf(selected_file_path):
    """读取并编码PDF文件"""
    with open(selected_file_path, 'rb') as file:
        file_data = file.read()
        pdf_content = base64.b64encode(file_data).decode('utf-8')
    return pdf_content

def run_command(window, command):
    """运行命令并实时输出结果"""
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                log_output(window, output)
        rc = process.poll()
        if rc == 0:
            log_output(window, "pdf_reader.py 已成功打包为可执行文件")
            reset_pdf_context()
        else:
            log_output(window, f"打包过程中发生错误，退出码: {rc}")
    except Exception as e:
        log_output(window, f"打包过程中发生错误: {e}")

def pack_pdf(selected_file_path, window):
    """打包PDF文件"""
    log_output(window, '')
    if not validate_file(selected_file_path):
        return
    
    pdf_content = encode_pdf(selected_file_path)
    set_pdf_context(pdf_content)
    log_output(window, f"文件 {selected_file_path} 已打包并设置到 pdf_context")
    
    build_dir = './build'
    dist_dir = './dist'
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(dist_dir, exist_ok=True)
    
    command = [
        'pyinstaller',
        '-w',
        '--onefile',
        '--distpath', dist_dir,
        '--workpath', build_dir,
        '--specpath', build_dir,
        'pdf_reader.py'
    ]
    log_output(window, f"执行命令: {' '.join(command)}")
    run_command(window, command)

# 事件循环
while True:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, '-EXIT-'):
        break
    elif event == '-PACK-':
        selected_file_path = values['-FILEPATH-']
        threading.Thread(target=pack_pdf, args=(selected_file_path, window)).start()
    elif event == '-RESET-':
        reset_pdf_context()
        log_output(window, "pdf_context 已重置为空值")
    elif event == '-TEST-':
        selected_file_path = values['-FILEPATH-']
        if validate_file(selected_file_path):
            pdf_content = encode_pdf(selected_file_path)
            pdf_document = read1pdf(pdf=pdf_content)
            display_pdf(pdf_document)
        else:
            log_output(window, "无法读取 PDF 内容")

# 关闭窗口
window.close()