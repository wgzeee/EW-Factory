import pandas as pd
import os
import matplotlib.pyplot as plt

def extract_geo_data(csv_file_path, province_name):
    """
    从CSV文件中提取指定省份的电厂容量和经纬度信息
    
    参数:
        csv_file_path (str): CSV文件的路径
        province_name (str): 省份名称（中文或英文）
        
    返回:
        tuple: (Capacity, Latitude, Longitude) 包含电厂容量和经纬度信息的数组
    """
    chinese_province_names = ['河北省', '山西省', '辽宁省','吉林省','黑龙江省',
                     '江苏省','浙江省','安徽省','福建省','江西省','山东省','河南省',
                     '湖北省','湖南省','广东省','海南省','四川省','贵州省','云南省',
                     '陕西省','甘肃省','青海省','台湾省','内蒙古自治区','广西壮族自治区',
                     '西藏自治区','宁夏回族自治区','新疆维吾尔自治区','北京市','天津市',
                     '重庆市','上海市']
    english_province_names = ['Hebei', 'Shanxi', 'Liaoning', 'Jilin', 'Heilongjiang',
                      'Jiangsu', 'Zhejiang', 'Anhui', 'Fujian', 'Jiangxi', 'Shandong', 'Henan',
                      'Hubei', 'Hunan', 'Guangdong', 'Hainan', 'Sichuan', 'Guizhou', 'Yunnan',
                      'Shaanxi', 'Gansu', 'Qinghai', 'Taiwan', 'Inner Mongolia', 'Guangxi',
                      'Tibet', 'Ningxia', 'Xinjiang', 'Beijing', 'Tianjin',
                      'Chongqing', 'Shanghai']
    
    # 将中文省份名转换为英文名
    if province_name in chinese_province_names:
        province_name = english_province_names[chinese_province_names.index(province_name)]
    elif province_name not in english_province_names:
        print(f"错误: 未找到省份 '{province_name}' 的英文名称")
        return None, None, None
    
    if not os.path.exists(csv_file_path):
        print(f"错误: 文件 '{csv_file_path}' 不存在")
        return None, None, None
        
    # 读取CSV文件
    print(f"正在读取文件: {csv_file_path}")
    try:
        # 尝试不同的编码方式读取文件
        encodings = ['utf-8', 'gbk', 'latin1']
        for encoding in encodings:
            try:
                df = pd.read_csv(csv_file_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            print("错误: 无法解码文件，请检查文件编码")
            return None, None, None
    except Exception as e:
        print(f"读取文件时出错: {str(e)}")
        return None, None, None
    
    # 检查必要的列是否存在
    required_columns = ['Capacity (MW)', 'Latitude', 'Longitude', 'State/Province', 'Status', 'Start year']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"错误: CSV文件缺少以下列: {', '.join(missing_columns)}")
        return None, None, None
    
    try:
        # 使用布尔索引筛选数据
        # 注意: 在pandas中，多个条件需要用括号分别括起来，并用 & 连接
        filtered_df = df[(df['State/Province'] == province_name) & 
                         (df['Status'] == 'operating') & 
                         (df['Start year'] != 2025)]
        
        if filtered_df.empty:
            print(f"警告: 未找到符合条件的电厂数据（省份: {province_name}，状态: operating，非2025年启动）")
            return [], [], []
        
        # 提取所需数据
        capacity = filtered_df['Capacity (MW)'].values
        latitude = filtered_df['Latitude'].values
        longitude = filtered_df['Longitude'].values
        
        print(f"成功提取 {len(capacity)} 个电厂的数据")
        return capacity, longitude, latitude
    
    except Exception as e:
        print(f"处理数据时出错: {str(e)}")
        return None, None, None



if __name__ == "__main__":
    csv_file_path = "C:\\Users\\wgzee\\Desktop\\China_solar_power_2025.2.csv"
    province_name = "山东省"
    capacity, longitude, latitude = extract_geo_data(csv_file_path, province_name)