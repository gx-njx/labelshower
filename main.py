import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QFileDialog, QLabel, QScrollArea, QListWidget, QHBoxLayout, QListWidgetItem
from PyQt5.QtCore import Qt, QMimeData, QPoint, QSize
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import os
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QLineEdit, QPushButton
from PyQt5.QtWidgets import QMenu, QColorDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import gc
from PIL import Image
import json
from collections import defaultdict

class ImageApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.image_index = 0
        self.image_folders = []
        self.current_images = [None] * 100  # 初始化为100个空值，对应100个图像位置
        self.colormap = None  # 默认的colormap
        # self.colorlist = [
        #                 [128, 128, 128],
        #                 [204,120,34], # farmland
        #                 [0, 128, 0], # trees
        #                 [0, 128, 0], # grass -> trees
        #                 [0, 0, 128], # water
        #                 [128, 0, 0], # Artificial surface
        #                 ]
        self.colorlist = [
                        [255, 0, 0],
                        [255, 0, 255],
                        [0, 0, 255],
                        [0, 255, 255],
                        [0, 255, 0],
                        [255, 255, 0],
                    ]
        self.plot_titles = []
        # 加载上次保存的文件夹路径
        self.load_folders()
        # 初始化颜色列表显示
        self.show_color_list()
        
    def initUI(self):
        self.setWindowTitle('Image Viewer')
        self.setGeometry(100, 100, 800, 600)

        # 设置接受拖放
        self.setAcceptDrops(True)

        # 创建主窗口布局
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        
        # 使用 QSplitter 使得侧边栏宽度可调
        splitter = QSplitter(Qt.Horizontal, self.main_widget)
        
        # 左侧列表栏和按钮
        left_widget = QWidget()  # 创建一个容器用于放置左侧内容
        left_layout = QVBoxLayout(left_widget)  # 竖直布局
        
        self.folder_list = QListWidget()
        # 启用拖放功能
        self.folder_list.setDragDropMode(QListWidget.InternalMove)
        self.folder_list.setDefaultDropAction(Qt.MoveAction)
        left_layout.addWidget(self.folder_list)  # 添加到左侧布局
        
        # 创建按钮组并添加到左侧布局
        button_layout_1 = QHBoxLayout()
        
        self.load_button = QPushButton('选择文件夹', self)
        self.load_button.clicked.connect(self.select_folder)
        button_layout_1.addWidget(self.load_button, alignment=Qt.AlignCenter)
        
        self.clear_button = QPushButton('清空文件夹', self)
        self.clear_button.clicked.connect(self.clear_folders)
        button_layout_1.addWidget(self.clear_button, alignment=Qt.AlignCenter)
        
        left_layout.addLayout(button_layout_1)

        button_layout_2 = QHBoxLayout()
        
        self.back_button = QPushButton('上一张', self)
        self.back_button.clicked.connect(self.show_back_image)
        button_layout_2.addWidget(self.back_button, alignment=Qt.AlignCenter)
        
        self.next_button = QPushButton('下一张', self)
        self.next_button.clicked.connect(self.show_next_image)
        button_layout_2.addWidget(self.next_button, alignment=Qt.AlignCenter)
        
        left_layout.addLayout(button_layout_2)

        button_layout_3 = QHBoxLayout()
        
        self.save_button = QPushButton('保存图像', self)
        self.save_button.clicked.connect(self.save_current_image)
        button_layout_3.addWidget(self.save_button, alignment=Qt.AlignCenter)
        
        self.save_all_button = QPushButton('保存所有子图', self)
        self.save_all_button.clicked.connect(self.save_all_subplots)
        button_layout_3.addWidget(self.save_all_button, alignment=Qt.AlignCenter)
        
        left_layout.addLayout(button_layout_3)
        
        # 添加颜色列表显示
        self.color_list_widget = QListWidget()
        left_layout.addWidget(self.color_list_widget)
        
        # 添加到分割器
        splitter.addWidget(left_widget)  

        # 右侧图像区域
        right_widget = QWidget()  # 创建一个容器用于放置右侧内容
        right_layout = QVBoxLayout(right_widget)  # 竖直布局
        
        # 创建空的Figure对象
        self.fig = Figure(figsize=(12, 12))  # 你可以选择一个默认的尺寸
        self.canvas = FigureCanvas(self.fig)
        right_layout.addWidget(self.canvas)
        
        splitter.addWidget(right_widget)  # 添加到分割器

        # 设置主窗口的布局为 QSplitter
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.addWidget(splitter)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self.show_back_image()
        elif event.key() == Qt.Key_Down:
            self.show_next_image()
        elif event.key() == Qt.Key_Left:
            self.show_back_image()
        elif event.key() == Qt.Key_Right:
            self.show_next_image()
        else:
            super().keyPressEvent(event)

    def show_color_list(self):
        """显示颜色列表"""
        self.color_list_widget.clear()
        for i, color in enumerate(self.colorlist, start=1):
            item = QListWidgetItem(self.color_list_widget)
            widget = ColorItem(color, i)
            item.setSizeHint(widget.sizeHint())
            self.color_list_widget.setItemWidget(item, widget)

    def save_folders(self):
        """保存当前已加载的文件夹路径和颜色列表为 JSON 格式"""
        data = {
            'image_folders': self.image_folders,
            'colorlist': self.colorlist,
            'plot_titles': self.plot_titles
        }
        
        with open('folders.json', 'w') as f:
            json.dump(data, f, indent=4)
        print("文件夹路径和颜色列表已保存")

    def load_folders(self):
        """加载上次保存的文件夹路径和颜色列表"""
        try:
            with open('folders.json', 'r') as f:
                data = json.load(f)
                self.image_folders = data.get('image_folders', [])
                self.colorlist = data.get('colorlist', [
                    [255, 0, 0],
                    [255, 0, 255],
                    [0, 0, 255],
                    [0, 255, 255],
                    [0, 255, 0],
                    [255, 255, 0]
                ])
                self.plot_titles = data.get('plot_titles', [])
                
                # 将文件夹添加到 QListWidget
                for folder in self.image_folders:
                    self.folder_list.addItem(folder)
                self.load_images()
                print("文件夹路径和颜色列表已加载")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"没有找到或无法加载文件夹路径和颜色列表文件: {e}")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder and folder not in self.image_folders:
            self.image_folders.append(folder)
            self.folder_list.addItem(folder)
            self.load_images()
            
    def load_images(self):
        # 清除现有的子图
        if hasattr(self,'axes'):
            for ax in self.axes.flatten():
                ax.clear()
        
        # 根据文件夹数量重新创建子图
        self.fig.clear()  # 清除当前Figure中的所有内容
        num_folders = len(self.image_folders)
        rows = int(np.ceil(np.sqrt(num_folders)))
        cols = int(np.ceil(num_folders / rows))
        self.axes = self.fig.subplots(rows, cols, squeeze=False)  # 保持axes为2D数组

        # for i, (ax, folder) in enumerate(zip(self.axes.flatten(), self.image_folders)):
        #     images_in_folder = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.png') or f.endswith('.tif')]
        #     if images_in_folder:  # 如果文件夹中有图片
        #         self.current_images[i] = sorted(images_in_folder)
        #         # self.image_index = 0  # 重置索引
        #     else:
        #         self.current_images[i] = None  # 如果没有图片则设置为None
                
        # # 提取同名图像，将同名图像放在同一位置
            # 存储所有文件夹中出现的基本文件名及其对应的完整路径
        all_names = defaultdict(set)
        # 存储每个文件夹中的图像
        self.current_images = []

        for folder in self.image_folders:
            images_in_folder = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.png') or f.endswith('.tif')]
            if images_in_folder:  # 如果文件夹中有图片
                # 获取基本文件名（无扩展名）
                base_names = {os.path.splitext(os.path.basename(f))[0]: f for f in images_in_folder}
                # 更新全局的文件名集合
                for base_name, path in base_names.items():
                    all_names[base_name].add(path)
                # 保存当前文件夹的图像列表
                self.current_images.append(sorted(images_in_folder, key=lambda x: os.path.splitext(os.path.basename(x))[0]))
            else:
                self.current_images.append(None)  # 如果没有图片则设置为None

        # 找出所有文件夹中共有的文件名
        common_names = {name for name, paths in all_names.items() if len(paths) == num_folders}

        # 重组current_images，将共有文件名排在前面
        for i, images in enumerate(self.current_images):
            if images is not None:
                # 分离共有文件和其他文件
                common_files = [f for f in images if os.path.splitext(os.path.basename(f))[0] in common_names]
                unique_files = [f for f in images if os.path.splitext(os.path.basename(f))[0] not in common_names]
                # 重组列表
                self.current_images[i] = common_files + unique_files
                
        self.update_images()

    
    def colour_code_label(self, label, label_values):
        label, colour_codes = np.array(label), np.array(label_values)
        if len(label.shape) == 3:
            label = np.argmax(label, axis=2)  # [HWC] -> [HW]
        color_label = np.zeros((label.shape[0], label.shape[1], 3), dtype=np.uint8)
        mask = label < len(colour_codes)
        color_label[mask] = colour_codes[label[mask].astype(int)]
        return color_label

    def update_images(self):
        # 清除每个子图中的旧图像数据
        for ax in self.axes.flatten():
            ax.clear()
            
        if not any(self.current_images):
            return
        i=1
        for ax, image_paths in zip(self.axes.flatten(), self.current_images):
            if image_paths is None or not image_paths:
                continue
            image_path = image_paths[self.image_index % len(image_paths)]
            # img = plt.imread(image_path)
            img = Image.open(image_path)
            img = np.array(img)
            if img.ndim == 2:  # 如果图像是2维的（灰度图像）
                if self.colorlist is not None:
                    img=self.colour_code_label(img, self.colorlist)
                    ax.imshow(img)
                else:
                    ax.imshow(img)
            else:  # 如果图像是3维的（彩色图像）
                ax.imshow(img)
            
            # 关闭坐标轴
            ax.axis('off')
            
            # 设置图注
            if self.plot_titles:
                ax.set_title(self.plot_titles[i-1])
            else:
                ax.set_title(str(i)+':'+os.path.basename(image_path))
            i+=1
            
        # 隐藏多余的子图
        for ax in self.axes.flatten()[len(self.image_folders):]:
            ax.axis('off')

        # 调整布局
        self.fig.tight_layout()
        # 刷新画布
        self.canvas.draw()
        # 强制垃圾回收
        gc.collect()

    def clear_folders(self):
        """清空当前文件夹路径及相关数据"""
        # 清空文件夹列表
        self.image_folders.clear()
        
        # 清空左侧列表栏
        self.folder_list.clear()
        
        # 重置当前图像列表
        self.current_images = [None] * 100  # 重新初始化为100个空值
        
        # 清除Figure中的所有内容
        self.fig.clear()
        
        # 如果有axes属性，则清除axes
        if hasattr(self, 'axes'):
            for ax in self.axes.flatten():
                ax.clear()
        
        # 更新UI
        self.update_images()

    def save_current_image(self, file_path=None):
        if not any(self.current_images):
            return
        if file_path is None:
            # 弹出文件保存对话框，让用户选择保存位置
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存图像", "", "PNG files (*.png);;All Files (*)"
            )
        if file_path:
            # 确保文件扩展名是.png
            if not file_path.lower().endswith('.png'):
                file_path += '.png'
            # 保存当前的 Figure 到指定的路径
            self.fig.savefig(file_path, bbox_inches='tight')
            print(f"图像已保存到: {file_path}")
        
    def save_all_subplots(self):
        # 选择保存目录
        dir_path = QFileDialog.getExistingDirectory(self, "选择保存文件夹")
        if not dir_path:
            return  # 如果用户取消了对话框

        for i, (ax, image_paths) in enumerate(zip(self.axes.flatten(), self.current_images)):
            if image_paths is None or not image_paths:
                continue  # 跳过空的子图

            # 获取当前显示的图像路径
            current_image_path = image_paths[self.image_index % len(image_paths)]
            base_name = os.path.splitext(os.path.basename(current_image_path))[0]
            file_name = f"{base_name}_ax{i+1}.png"  # 序号从1开始
            file_path = os.path.join(dir_path, file_name)

            # 读取图像
            img = plt.imread(current_image_path)

            if img.ndim == 2:  # 如果是2维图（灰度图）
                if self.colorlist is not None:
                    img = self.colour_code_label(img, self.colorlist)
                else:
                    cmap = self.create_colormap(self.colormap)
                    # 将灰度图转换为RGB图
                    img = cmap(img)[:, :, :3]  # 取前三个通道（RGB），忽略alpha通道
            else:  # 如果是3维图（彩色图）
                pass  # 无需转换

            # 将NumPy数组转换为PIL图像
            pil_img = Image.fromarray(img.astype(np.uint8))

            # 保存图像
            pil_img.save(file_path)

            print(f"子图已保存到: {file_path}")
            
        self.save_current_image(os.path.join(dir_path, f"{base_name}_all.png"))
        
    def show_back_image(self):
        if any(self.current_images):
            self.image_index -= 1
            self.image_index = 0 if self.image_index < 0 else self.image_index
            self.update_images()
            
    def show_next_image(self):
        if any(self.current_images):
            self.image_index += 1
            self.update_images()

    # 拖放事件处理
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        file_paths = [url.toLocalFile() for url in urls]
        self.handle_dropped_files(file_paths)

    def handle_dropped_files(self, file_paths):
        folders = [path for path in file_paths if os.path.isdir(path)]
        if folders:
            for folder in folders:
                if folder not in self.image_folders:
                    self.image_folders.append(folder)
                    self.folder_list.addItem(folder)
            self.load_images()

    def exit_application(self):
        """退出应用程序前执行的清理操作"""
        self.save_folders()
        self.close()

class ColorItem(QWidget):
    def __init__(self, color, number, parent=None):
        super().__init__(parent)
        self.color = color
        self.number = number
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建一个 QLabel 显示颜色块
        self.color_label = QLabel(self)
        self.color_label.setStyleSheet(f"background-color: rgb({', '.join(map(str, self.color))});")
        self.color_label.setContextMenuPolicy(Qt.CustomContextMenu)  # 允许自定义上下文菜单
        self.color_label.customContextMenuRequested.connect(self.show_color_menu)  # 连接信号到槽

        # 创建一个 QLabel 显示数字
        self.number_label = QLabel(f"{self.number}", self)
        self.number_label.setAlignment(Qt.AlignCenter)  # 使数字居中

        # 将颜色块和数字标签添加到布局中，并设置它们的 stretch 因子
        layout.addWidget(self.number_label, 1)  # 1 表示 stretch 因子
        layout.addWidget(self.color_label, 1)  # 1 表示 stretch 因子

        self.setLayout(layout)

    def show_color_menu(self, position):
        """显示颜色选择菜单"""
        menu = QMenu(self)
        change_color_action = menu.addAction("更改颜色")
        action = menu.exec_(self.color_label.mapToGlobal(position))
        
        if action == change_color_action:
            self.change_color()

    def change_color(self):
        """打开颜色选择对话框并更新颜色块的颜色"""
        color = QColorDialog.getColor(QColor(*self.color), self, "选择颜色")
        if color.isValid():
            self.color = [color.red(), color.green(), color.blue()]
            self.color_label.setStyleSheet(f"background-color: rgb({', '.join(map(str, self.color))});")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageApp()
    ex.show()
    
    # 连接 aboutToQuit 信号以在退出时调用 exit_application 方法
    app.aboutToQuit.connect(ex.exit_application)
    
    sys.exit(app.exec_())