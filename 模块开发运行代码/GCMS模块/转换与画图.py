import os
import subprocess
import matplotlib.font_manager as font_manager
import pymzml
import csv
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider


def convert_to_mzml(input_folder, output_file):
    """
    将质谱数据文件转换为mzML格式

    参数:
        input_folder: 输入数据文件夹路径
        output_file: 输出mzML文件路径
    """
    # Check if msconvert.exe exists
    msconvert_path = 'C:\\Program Files\\ProteoWizard\\ProteoWizard 3.0.25323.6de0b61/msconvert.exe'  # 替换为实际的msconvert.exe路径
    if not os.path.exists(msconvert_path):
        print("msconvert.exe not found. Please make sure msconvert.exe is in the specified directory.")
        return

    # Check if the input folder exists
    if not os.path.exists(input_folder):
        print("Input folder not found.")
        return

    # Run msconvert.exe to convert the data to mzml format
    subprocess.run([msconvert_path, '--mzML', input_folder, '-o', os.path.dirname(output_file)])

    print(f"Conversion successful. MzML file saved as: {output_file}")


class GCMSPlotter:
    """
    GCMS数据绘图类，用于可视化mzML格式的质谱数据和CSV格式的色谱数据
    """

    def __init__(self, mzml_file_path, csv_file_path):
        self.mzml_file_path = mzml_file_path
        self.csv_file_path = csv_file_path
        self.id_to_x = {}
        self.x_data = []
        self.y_data = []

        # 初始化读取 mzML 文件和 CSV 文件
        self.read_mzml_file()
        self.read_csv_file()

        # 创建画布和子图
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(12, 6))
        self.setup_plot()

    def read_mzml_file(self):
        """读取 mzML 文件并建立 ID 与 X 值的映射"""
        run = pymzml.run.Reader(self.mzml_file_path)
        for spectrum in run:
            spectrum_id = spectrum['id']
            # 更安全地获取扫描时间，处理可能的None值
            scan_time = None

            # 方法1: 尝试使用scan_time_in_minutes方法
            try:
                if hasattr(spectrum, 'scan_time_in_minutes'):
                    scan_time = spectrum.scan_time_in_minutes()
            except:
                pass

            # 方法2: 如果上述方法不可用，尝试从属性获取
            if scan_time is None:
                scan_time = spectrum.get('scan time', None)

            # 方法3: 尝试其他可能的时间属性名
            if scan_time is None:
                # 尝试常见的保留时间属性名
                for time_attr in ['retention time', 'scan_time', 'rt', 'retentionTime']:
                    if time_attr in spectrum:
                        scan_time = spectrum[time_attr]
                        break

            # 记录有效的时间值，跳过None值
            if scan_time is not None:
                self.id_to_x[spectrum_id] = scan_time
                print(f"Spectrum ID: {spectrum_id}, Scan time: {scan_time}")
            else:
                print(f"警告: Spectrum ID {spectrum_id} 没有可用的扫描时间信息")

    def read_csv_file(self):
        """读取 CSV 文件数据"""
        with open(self.csv_file_path, mode='r', newline='') as csv_file:
            csv_reader = csv.reader(csv_file)
            headers = next(csv_reader, None)
            if headers is not None:
                print(f"标题行已读取: {headers}")
            for row in csv_reader:
                try:
                    x = float(row[0])
                    y = float(row[1])
                    self.x_data.append(x)
                    self.y_data.append(y)
                    print(f"读取数据: X={x}, Y={y}")
                except ValueError as e:
                    print(f"在读取数据时遇到错误: {e}")
                    print(f"有问题的数据行: {row}")

    def setup_plot(self):
        """初始化图表设置"""
        # 检查是否有有效的数据
        if not self.x_data or not self.y_data:
            print("错误: 没有有效的CSV数据可绘制")
            return

        # 绘制 CSV 数据曲线图
        self.ax1.plot(self.x_data, self.y_data, marker='o')
        self.ax1.set_title('CSV数据色谱图')
        self.ax1.set_xlabel('X轴标签')
        self.ax1.set_ylabel('Y轴标签')
        self.ax1.grid(True)

        # 设置中文字体
        self.set_chinese_font()

        # 添加滑动滚轴（仅在有效数据存在时）
        if self.x_data:
            ax_slider = plt.axes([0.1, 0.02, 0.65, 0.03])
            self.slider = Slider(ax_slider, 'X轴滑动', min(self.x_data), max(self.x_data), valinit=min(self.x_data))
            self.slider.on_changed(self.update_plot)

    def set_chinese_font(self):
        """设置中文字体"""
        fonts = [f.name for f in font_manager.fontManager.ttflist]
        for font in fonts:
            if 'SimHei' in font:
                plt.rcParams['font.sans-serif'] = [font]
                plt.rcParams['axes.unicode_minus'] = False
                break
        else:
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            print("没有找到支持中文的字体，请确保你的系统上安装了支持中文的字体。")

    def update_plot(self, val):
        """更新曲线图和质谱图"""
        x_val = self.slider.val

        # 更新左侧色谱图
        self.ax1.clear()
        self.ax1.plot(self.x_data, self.y_data, marker='o')
        self.ax1.set_title('CSV数据色谱图')
        self.ax1.set_xlabel('X轴标签')
        self.ax1.set_ylabel('Y轴标签')
        self.ax1.grid(True)
        self.ax1.axvline(x=x_val, color='r', linestyle='--')
        self.ax1.text(x_val, max(self.y_data) * 0.9, f'X={x_val:.2f}', color='r')

        # 查找滑动滚轴当前值对应的 ID（添加None值检查）
        matching_id = self.find_matching_id(x_val)

        # 根据是否找到匹配的ID来更新质谱图
        if matching_id is not None:
            self.plot_mass_spectrum(matching_id)
        else:
            self.show_no_data()

        plt.draw()

    def find_matching_id(self, x_val):
        """查找滑动滚轴当前值对应的 ID，添加None值检查"""
        closest_id = None
        min_diff = float('inf')

        for spectrum_id, x_value in self.id_to_x.items():
            # 关键修复：检查x_value是否为None
            if x_value is None:
                continue

            try:
                diff = abs(x_value - x_val)
                if diff < min_diff and diff < 0.01:  # 设置阈值
                    min_diff = diff
                    closest_id = spectrum_id
            except TypeError as e:
                print(f"类型错误跳过 spectrum_id {spectrum_id}: {e}")
                continue

        return closest_id

    def plot_mass_spectrum(self, matching_id):
        """根据匹配的 ID 绘制质谱图"""
        mz_values = []
        intensity_values = []

        try:
            run = pymzml.run.Reader(self.mzml_file_path)
            for spectrum in run:
                if spectrum.ID == matching_id:
                    # 使用更安全的方式获取peaks
                    peaks = spectrum.peaks("centroided")
                    if peaks is not None:
                        for peak in peaks:
                            if len(peak) >= 2:  # 确保peak包含mz和intensity
                                mz_values.append(peak[0])
                                intensity_values.append(peak[1])
                    break
        except Exception as e:
            print(f"读取质谱数据时出错: {e}")
            self.show_no_data()
            return

        # 绘制质谱图（仅在有效数据存在时）
        if mz_values and intensity_values:
            self.ax2.clear()
            self.ax2.bar(mz_values, intensity_values, width=0.1)  # 设置适当的宽度
            self.ax2.set_title(f'质谱图 (ID: {matching_id})')
            self.ax2.set_xlabel('m/z')
            self.ax2.set_ylabel('强度')
            self.ax2.grid(True)
            if mz_values:  # 避免空列表的min/max操作
                self.ax2.set_xlim(min(mz_values) - 1, max(mz_values) + 1)
            if intensity_values:
                self.ax2.set_ylim(0, max(intensity_values) * 1.1)
        else:
            self.show_no_data(f"ID {matching_id} 无质谱数据")

    def show_no_data(self, message='未找到匹配的数据'):
        """显示没有数据的提示信息"""
        self.ax2.clear()
        self.ax2.set_title('无数据')
        self.ax2.text(0.5, 0.5, message,
                      horizontalalignment='center',
                      verticalalignment='center',
                      transform=self.ax2.transAxes)
        self.ax2.set_xlim(0, 1)
        self.ax2.set_ylim(0, 1)
        self.ax2.grid(False)

    def show(self):
        """显示图表"""
        # 检查是否有有效的数据再显示
        if not self.id_to_x:
            print("警告: 没有从mzML文件中读取到有效的谱图数据")
        if not self.x_data:
            print("错误: 没有有效的CSV数据")
            return

        plt.tight_layout()
        plt.show()


def main():
    """
    主函数，演示整个GCMS数据处理流程
    """
    # 步骤1: 转换数据为mzML格式
    input_folder = r"D:\MassHunter\GCMS\1\data\20241204\Test.D"  # 替换为实际的文件夹路径
    output_file = "D:/Python项目/GCMS模块本地客户端版本/Mzml格式文件/Test.mzML"  # 替换为实际的输出文件路径

    print("开始转换数据为mzML格式...")
    convert_to_mzml(input_folder, output_file)

    # 步骤2: 可视化GCMS数据
    mzml_file_path = r'D:/Python项目/GCMS模块本地客户端版本/Mzml格式文件/Test.mzML'
    csv_file_path = r'D:\MassHunter\GCMS\1\data\20241204\Test.D\tic_front.csv'

    print("开始可视化GCMS数据...")
    plotter = GCMSPlotter(mzml_file_path, csv_file_path)
    plotter.show()


if __name__ == '__main__':
    # 可以选择直接运行主函数，或者分别调用各个功能

    # 运行完整流程（转换+可视化）
    main()
