import json
import urllib.request
import urllib.parse
import urllib.error


class PeakFinder:
    def __init__(self, base_url):
        self.base_url = base_url

    def find_peaks_with_filter(self, data_dir, relative_area_percent=1.0):
        """
        使用面积百分比过滤的查找峰方法
        :param data_dir: 数据文件夹路径(.d结尾)
        :param relative_area_percent: 相对面积百分比阈值(0-100)，例如1.0表示只保留面积≥1%的峰
        :return: 峰信息列表
        """
        # 使用过滤参数，只保留显著峰
        filter_params = {
            "msLevel": "All",
            "scanType": "All",
            "chromatogramType": "TotalIon",
            "smoothFunction": "Gaussian",
            "smoothGaussianWidth": 5,
            "smoothFunctionWidth": 15,
            "relativeAreaPercent": relative_area_percent / 100  # 转换为0-1范围
        }

        # 构造请求数据
        request_data = {
            "dataDir": data_dir,
            "filter": filter_params
        }

        # 转换为JSON字符串
        json_data = json.dumps(request_data).encode('utf-8')

        # 构造URL
        url = f"{self.base_url}/qual/findPeaks"

        # 设置请求头
        headers = {'Content-Type': 'application/json'}

        print("开始查找峰(使用面积过滤)...")
        print(f"数据路径: {data_dir}")
        print(f"相对面积阈值: ≥{relative_area_percent}%")

        # 创建请求对象
        req = urllib.request.Request(url, headers=headers, data=json_data, method='POST')

        try:
            # 发送请求
            with urllib.request.urlopen(req) as response:
                data = response.read().decode('utf-8')
                peaks_data = json.loads(data)

                print("✓ 峰查找成功!")
                print(f"找到 {len(peaks_data)} 个显著峰")
                print("\n显著峰信息详情:")
                print("-" * 80)

                # 计算总面积用于显示相对百分比
                total_area = sum(peak.get('area', 0) for peak in peaks_data) if peaks_data else 0

                # 打印每个峰的详细信息
                for i, peak in enumerate(peaks_data):
                    area = peak.get('area', 0)
                    relative_percent = (area / total_area * 100) if total_area > 0 else 0

                    print(f"峰 {i + 1}:")
                    print(f"  中心RT时间 (centerX): {peak.get('centerX', 0):.4f}")
                    print(f"  面积 (area): {area:.2f}")
                    # print(f"  相对面积: {relative_percent:.2f}%")
                    print(f"  起始时间 (startX): {peak.get('startX', 0):.4f}")
                    print(f"  结束时间 (endX): {peak.get('endX', 0):.4f}")
                    print(f"  峰宽 (width): {peak.get('width', 0):.4f}")
                    print(f"  基线是否线性: {peak.get('baselineIsLinear', 'N/A')}")
                    print()

                return peaks_data

        except urllib.error.HTTPError as e:
            error_msg = f'HTTP错误: {e.code} - {e.reason}'
            try:
                error_data = e.read().decode('utf-8')
                error_json = json.loads(error_data)
                error_msg += f"\n错误代码: {error_json.get('errorCode', '未知')}"
                error_msg += f"\n错误信息: {error_json.get('errorMessage', '未知')}"
            except:
                error_msg += f"\n响应内容: {error_data}"

            print(f"✗ {error_msg}")
            return None

        except Exception as e:
            print(f"✗ 请求失败: {str(e)}")
            return None

    def find_peaks_simple(self, data_dir):
        """
        简化版的查找峰方法（不过滤小峰）
        """
        return self.find_peaks_with_filter(data_dir, relative_area_percent=0)


# 使用示例
if __name__ == '__main__':
    # 仪器控制器的基本URL
    BASE_URL = "http://192.168.58.125:8082"

    # 创建峰查找器实例
    peak_finder = PeakFinder(BASE_URL)

    # 您的数据文件路径
    DATA_FILE_PATH = r"D:\MassHunter\GCMS\1\data\20241204\Test.D"

    print("=" * 60)
    print("1. 使用面积过滤（只显示显著峰）")
    print("=" * 60)

    # 方法1：使用面积过滤，只显示面积≥1%的显著峰
    significant_peaks = peak_finder.find_peaks_with_filter(DATA_FILE_PATH, relative_area_percent=1.0)

    print("\n" + "=" * 60)
