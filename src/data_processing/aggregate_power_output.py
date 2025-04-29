import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import griddata
from src.models import f_solar_power
from src.models import f_wind_power

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


def find_nearest_grid_points_method1(lon_grid, lat_grid, longitude, latitude):
    """
    方法1：向量化计算所有电厂到所有网格点的距离
    
    参数:
        lon_grid (ndarray): 经度网格
        lat_grid (ndarray): 纬度网格
        longitude (ndarray): 电厂经度数组
        latitude (ndarray): 电厂纬度数组
        
    返回:
        tuple: 包含每个电厂最近网格点的行列索引
    """
    # 将网格展平为二维点集
    grid_points = np.column_stack((lon_grid.ravel(), lat_grid.ravel()))  # shape: [nx*ny, 2]
    plant_points = np.column_stack((longitude, latitude))                # shape: [plant_count, 2]
    
    # 向量化计算所有电厂到所有网格点的距离矩阵
    diffs = grid_points[:, None, :] - plant_points[None, :, :]           # shape: [nx*ny, plant_count, 2]
    dist_matrix = np.sqrt(np.sum(diffs**2, axis=2))                     # shape: [nx*ny, plant_count]
    
    # 找到每个电厂最近的网格索引
    nearest_flat_indices = np.argmin(dist_matrix, axis=0)               # shape: [plant_count]
    nearest_indices = np.unravel_index(nearest_flat_indices, lon_grid.shape)  # 转为二维索引
    
    # 转换为列表形式，与其他方法保持一致的返回格式
    return [(nearest_indices[0][i], nearest_indices[1][i]) for i in range(len(longitude))]


def find_nearest_grid_points_method2(lon_grid, lat_grid, longitude, latitude):
    """
    方法2：假设网格均匀分布，直接计算最近网格索引
    
    参数:
        lon_grid (ndarray): 经度网格
        lat_grid (ndarray): 纬度网格
        longitude (ndarray): 电厂经度数组
        latitude (ndarray): 电厂纬度数组
        
    返回:
        list: 包含每个电厂最近网格点的行列索引
    """
    # 检查网格是否均匀分布
    lon_steps = lon_grid[1:, 0] - lon_grid[:-1, 0]
    lat_steps = lat_grid[0, 1:] - lat_grid[0, :-1]
    
    if not (np.allclose(lon_steps, lon_steps[0], rtol=1e-5) and np.allclose(lat_steps, lat_steps[0], rtol=1e-5)):
        print("警告: 网格不是均匀分布的，方法2可能不准确")
    
    # 计算网格步长
    lon_step = lon_grid[1, 0] - lon_grid[0, 0]
    lat_step = lat_grid[0, 1] - lat_grid[0, 0]
    
    # 计算每个电厂所在的网格行列号
    i = np.round((longitude - lon_grid[0, 0]) / lon_step).astype(int)
    j = np.round((latitude - lat_grid[0, 0]) / lat_step).astype(int)
    
    # 处理边界情况
    i = np.clip(i, 0, lon_grid.shape[0] - 1)
    j = np.clip(j, 0, lon_grid.shape[1] - 1)
    
    # 转换为列表形式，与其他方法保持一致的返回格式
    return [(i[k], j[k]) for k in range(len(longitude))]


def find_nearest_grid_points_method3(lon_grid, lat_grid, longitude, latitude):
    """
    方法3：循环计算每个电厂到所有网格点的距离
    
    参数:
        lon_grid (ndarray): 经度网格
        lat_grid (ndarray): 纬度网格
        longitude (ndarray): 电厂经度数组
        latitude (ndarray): 电厂纬度数组
        
    返回:
        list: 包含每个电厂最近网格点的行列索引
    """
    nearest_indices = []
    for i in range(len(longitude)):
        # 计算电厂到所有网格点的距离
        dist = np.sqrt((lon_grid - longitude[i])**2 + (lat_grid - latitude[i])**2)
        nearest_idx = np.unravel_index(np.argmin(dist), dist.shape)
        nearest_indices.append(nearest_idx)

    return nearest_indices


def extract_station_data(var_data, lon_grid, lat_grid, longitude, latitude, method=1):
    """
    提取电力场站位置的气象数据
    
    参数:
        var_data (ndarray): 形状为(时间, 纬度, 经度)的气象数据
        lon_grid (ndarray): 经度网格
        lat_grid (ndarray): 纬度网格
        longitude (ndarray): 电厂经度数组
        latitude (ndarray): 电厂纬度数组
        method (int): 计算最近网格点的方法，1=向量化计算，2=均匀网格直接计算，3=循环计算
        
    返回:
        tuple: (station_data, valid_nearest_indices)
            - station_data (ndarray): 形状为(时间, 电厂数量)的各电厂气象数据
            - valid_nearest_indices (list): 每个电厂对应的有效网格点索引
    """
    # 获取时间步长和电厂数量
    time_steps = var_data.shape[0]
    plant_count = len(longitude)
    
    # 初始化电厂气象数据数组
    station_data = np.zeros((time_steps, plant_count))
    
    # 根据选择的方法计算最近网格点
    if method == 1:
        nearest_indices = find_nearest_grid_points_method1(lon_grid, lat_grid, longitude, latitude)
    elif method == 2:
        nearest_indices = find_nearest_grid_points_method2(lon_grid, lat_grid, longitude, latitude)
    else:
        nearest_indices = find_nearest_grid_points_method3(lon_grid, lat_grid, longitude, latitude)
    
    # 检查第一个时间步的数据，处理NaN值
    first_time_var = var_data[0]
    valid_nearest_indices = []
    
    for i in range(plant_count):
        nearest_idx = nearest_indices[i]
        plant_var = first_time_var[nearest_idx]
        
        # 如果值为NaN，找最近的有效值
        if np.isnan(plant_var):
            print(f"警告: 场站{i}({longitude[i]},{latitude[i]})的气象值为NaN，尝试找最近的有效值")
            # 创建有效值掩码
            valid_mask = ~np.isnan(first_time_var)
            if np.any(valid_mask):
                # 向量化计算所有有效点到电厂的距离
                valid_points = np.where(valid_mask)
                valid_lons = lon_grid[valid_points]
                valid_lats = lat_grid[valid_points]
                
                # 计算电厂到所有有效点的距离
                distances = np.sqrt((valid_lons - longitude[i])**2 + (valid_lats - latitude[i])**2)
                
                # 找到最近的有效点索引
                min_dist_idx = np.argmin(distances)
                nearest_valid_idx = (valid_points[0][min_dist_idx], valid_points[1][min_dist_idx])
                valid_nearest_indices.append(nearest_valid_idx)
            else:
                print(f"警告: 经度：{longitude[i]}，纬度：{latitude[i]}附近没有有效值，该值设置为0")
                valid_nearest_indices.append(nearest_idx)  # 保持原索引，后续会处理为0
        else:
            valid_nearest_indices.append(nearest_idx)
    
    # 提取每个电厂在所有时间步的气象数据
    for i in range(plant_count):
        valid_idx = valid_nearest_indices[i]
        station_data[:, i] = var_data[:, valid_idx[0], valid_idx[1]]
    
    return station_data, valid_nearest_indices

def calculate_province_power_output(var_data, lon_grid, lat_grid, csv_file_path, 
                                    province_name, T=None, power_type='solar', method=1):
    """
    计算指定省份所有电力场站的聚合出力
    
    参数:
        var_data (ndarray): 形状为(时间, 纬度, 经度)的气象数据（光伏为辐射数据，风电为风速数据）
        lon_grid (ndarray): 经度网格
        lat_grid (ndarray): 纬度网格
        csv_file_path (str): CSV文件路径，包含电厂信息
        province_name (str): 省份名称
        T (ndarray, optional): 形状为(时间, 纬度, 经度)的温度数据，默认为None
        power_type (str): 发电类型，'solar'表示光伏，'wind'表示风电
        method (int): 计算最近网格点的方法，1=向量化计算，2=均匀网格直接计算，3=循环计算
        
    返回:
        tuple: (total_power_output, power_by_plant)
            - total_power_output (ndarray): 形状为(时间)的省级聚合出力数据，单位为MW
            - power_by_plant (ndarray): 形状为(时间, 电厂数量)的各电厂出力数据，单位为MW
    """
    # 提取省份电厂容量和位置信息
    capacity, longitude, latitude = extract_geo_data(csv_file_path, province_name)
    
    if capacity is None or len(capacity) == 0:
        print(f"错误: 无法获取 {province_name} 的电厂数据")
        return None, None
    
    # 获取时间步长和电厂数量
    time_steps = var_data.shape[0]
    plant_count = len(capacity)
    
    # 初始化电厂出力数组
    power_by_plant = np.zeros((time_steps, plant_count))
    
    # 提取各电厂位置的气象数据
    plant_var_data, valid_nearest_indices = extract_station_data(var_data, lon_grid, lat_grid, longitude, latitude, method)
    
    # 如果提供了温度数据，也提取各电厂位置的温度数据
    plant_temp_data = None
    if T is not None:
        plant_temp_data, _ = extract_station_data(T, lon_grid, lat_grid, longitude, latitude, method)
    
    # 计算每个电厂的出力
    for i in range(plant_count):
        try:
            # 根据发电类型计算容量系数
            if power_type.lower() == 'solar':
                # 光伏发电 - 使用太阳辐射数据
                if plant_temp_data is None:
                    capacity_factors = f_solar_power.f_solar_power_2(plant_var_data[:, i])
                else:
                    capacity_factors = f_solar_power.f_solar_power_with_temp(plant_var_data[:, i], plant_temp_data[:, i])
            elif power_type.lower() == 'wind':
                # 风力发电 - 使用风速数据
                capacity_factors = f_wind_power.f_wind_power(plant_var_data[:, i])
            else:
                raise ValueError(f"不支持的发电类型: {power_type}")

            # 计算实际出力（MW）= 容量系数 * 装机容量
            power_by_plant[:, i] = capacity_factors * capacity[i]
        except Exception as e:
            print(f"警告: 计算电厂 {i+1} 的出力时出错: {str(e)}")
            power_by_plant[:, i] = 0

    # 计算省级聚合出力
    # 计算总装机容量
    total_capacity = np.sum(capacity)
    # 计算总出力并按总装机容量归一化
    total_power_output = np.sum(power_by_plant, axis=1) / total_capacity

    print(f"成功计算 {province_name} 的 {plant_count} 个{power_type}电厂的归一化聚合出力")
    return total_power_output
