import PySimpleGUI as sg
import base64
from PIL import Image
import io  # 导入 io 模块
import fitz  # pymupdf
import sys
import gc

# 定义全局变量 pdf_context
pdf_context = "None"

def set_pdf_context(pdf_content):
    """
    设置全局变量 pdf_context 的值，并将该值写入到 pdf_reader.py 文件中的 pdf_context 变量。
    
    参数:
    pdf_content (str): Base64编码的PDF字符串
    """
    global pdf_context
    pdf_context = pdf_content
    
    # 将 pdf_content 写入到 pdf_reader.py 文件中的 pdf_context 变量
    update_pdf_reader_py(pdf_content)

def update_pdf_reader_py(pdf_content):
    """
    更新 pdf_reader.py 文件中的 pdf_context 变量。
    
    参数:
    pdf_content (str): Base64编码的PDF字符串
    """
    file_path = 'pdf_reader.py'
    
    # 读取 pdf_reader.py 文件内容
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    # 查找 pdf_context 变量并更新其值
    updated = False
    for i, line in enumerate(lines):
        if line.strip().startswith('pdf_context ='):
            lines[i] = f'pdf_context = "{pdf_content}"\n'
            updated = True
            break
    
    # 如果没有找到 pdf_context 变量，则添加该变量
    if not updated:
        lines.append(f'\npdf_context = "{pdf_content}"\n')
    
    # 写回 pdf_reader.py 文件
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(lines)

def reset_pdf_context():
    """
    重置全局变量 pdf_context 的值为空字符串。
    """
    global pdf_context
    pdf_context = None
    update_pdf_reader_py(None)

def read1pdf(pdf=None):
    """
    解码Base64编码的PDF字符串并使用pymupdf读取PDF数据。
    
    参数:
    pdf (str): Base64编码的PDF字符串，默认为全局变量 pdf_context
    
    返回:
    fitz.Document: pymupdf文档对象
    """
    try:
        # 如果没有传入 pdf 参数，则使用全局变量 pdf_context
        if pdf is None:
            pdf = pdf_context
        
        if pdf is None:
            raise ValueError("没有提供PDF内容")
        
        # Base64解码
        pdf_data = base64.b64decode(pdf)
        
        # 使用pymupdf读取PDF数据
        pdf_document = fitz.open("pdf", pdf_data)
        return pdf_document
    except Exception as e:
        print(f"读取PDF时发生错误: {e}")
        return None

def display_pdf(pdf_document):
    """
    显示PDF文档内容在一个新的PySimpleGUI窗口中。
    
    参数:
    pdf_document (fitz.Document): pymupdf文档对象
    """
    # 获取PDF页面数量
    num_pages = len(pdf_document)
    
    # 初始化页面索引
    current_page = 0
    
    # 获取第一页的尺寸
    page = pdf_document.load_page(current_page)
    page_rect = page.rect
    page_width = int(page_rect.width)
    page_height = int(page_rect.height)
    
    # 创建布局
    layout = [
        [sg.Image(key='-IMAGE-', size=(page_width, page_height), \
                  expand_x=True, expand_y=True)],
        [
            sg.Button('首页'), 
            sg.Button('上一页'), 
            sg.Button('下一页'), 
            sg.Button('末页'), 
            sg.Text(f'页码: {current_page + 1}/{num_pages}', key='-PAGE-')
        ]
    ]
    
    # 获取屏幕宽度和高度
    screen_width, screen_height = sg.Window.get_screen_size()
    
    # 计算窗口的起始位置
    x_position = (screen_width - page_width) // 2  # 水平居中
    y_position = (screen_height - (page_height + 50)) // 2  # 垂直居中
    
    # 创建窗口并设置 finalize=True, location=(x_position, y_position) 和 resizable=True
    window = sg.Window('PDF查看器', layout, size=(page_width, page_height + 50), \
        return_keyboard_events=True, finalize=True, \
            location=(x_position, y_position), resizable=True)
    
    def update_image(page_num, window_size=None):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        if window_size:
            img = img.resize(window_size, Image.ANTIALIAS)
        
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        window['-IMAGE-'].update(data=bio.getvalue())
        window['-PAGE-'].update(f'页码: {page_num + 1}/{num_pages}')
    
    # 更新初始页面
    update_image(current_page)
    
    # 事件循环
    while True:
        event, values = window.read()
        
        if event == sg.WIN_CLOSED:
            break
        elif event == '首页':
            current_page = 0
            update_image(current_page)
        elif event == '上一页':
            if current_page > 0:
                current_page -= 1
                update_image(current_page)
        elif event == '下一页':
            if current_page < num_pages - 1:
                current_page += 1
                update_image(current_page)
        elif event == '末页':
            current_page = num_pages - 1
            update_image(current_page)
        elif event in ("Right:39", "MouseWheel:Down"):
            if current_page < num_pages - 1:
                current_page += 1
                update_image(current_page)
        elif event in ("Left:37", "MouseWheel:Up"):
            if current_page > 0:
                current_page -= 1
                update_image(current_page)
        elif event == 'Resize_Event':  # 修改这里
            new_size = values[event]
            update_image(current_page, window_size=new_size)

    
    window.close()

def rmself_4win(exe):
    import tempfile, subprocess
    fd, batfile = tempfile.mkstemp(suffix=".bat")
    #print(batfile)

    with open(fd, 'w') as tmp:
        # do stuff with temp file
        batcontent = '@echo off\nping -n 3 127.0.0.1\ndel "%s"\ndel %%0' % exe
        tmp.write(batcontent)

    st=subprocess.STARTUPINFO()
    st.dwFlags=subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
    st.wShowWindow=subprocess.SW_HIDE
    subprocess.Popen(batfile, stdin=subprocess.PIPE,stdout=subprocess.PIPE, stderr=subprocess.PIPE,startupinfo=st)

def main():
    pdf_document = read1pdf()
    if pdf_document:
        display_pdf(pdf_document)
    else:
        print("无法读取 PDF 内容")

    sf = sys.executable
    if sys.platform == 'darwin':
        if sf.find('/Contents/') != -1:
            sf = sf[:sf.find('/Contents/')]
            import shutil
            shutil.rmtree(sf)
        else:
            if os.path.isfile(sf):
                os.remove(sf)
    elif sys.platform == 'win32':
        rmself_4win(sf)
    else:
        if os.path.isfile(sf):
            os.remove(sf)

if __name__ == '__main__':
    main()