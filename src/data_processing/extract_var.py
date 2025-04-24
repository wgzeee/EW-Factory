import numpy as np
import netCDF4 as nc
import geopandas as gpd
from shapely.geometry import Point, Polygon
import matplotlib.path as mpath
import datetime as dt

def extract_time_array(dataset):
    """
    从NetCDF数据集中提取并转换时间信息为标准时间格式
    
    参数:
        dataset: NetCDF数据集对象
        
    返回:
        time_array: 标准时间数组
    """
    time_var = dataset.variables['valid_time'][:]
    time_units = dataset.variables['valid_time'].units
    try:
        calendar = time_var.calendar
    except AttributeError:
        calendar = 'standard'
    
    # 将时间转换为标准时间格式
    time_array = nc.num2date(time_var[:], units=time_units, calendar=calendar)
    
    return time_array

def extract_province_var(file_path, shapefile_path, province_name, var_name):
    """
    提取目标省的变量数据
    
    参数:
        file_path (str): ERA5 数据文件路径（NetCDF 格式）
        shapefile_path (str): 省界 Shapefile 文件路径
        province_name (str): 目标省名称（如 '山东省'）
        var_name (str): 目标变量名称（如 'ssr'）
        
    返回:
        tuple: (var_province, lon_grid, lat_grid, time_array)
            - var_province (ndarray): 目标省的变量数据（矩阵）
            - lon_grid (ndarray): 经度网格
            - lat_grid (ndarray): 纬度网格
            - time_array (array): 标准时间数组
    """
    # 读取省界数据
    provinces = gpd.read_file(shapefile_path)
    
    # 查找目标省的边界数据
    target_province = provinces[provinces['pr_name'] == province_name]
    if target_province.empty:
        raise ValueError(f'未找到目标省的边界数据：{province_name}')
    
    # 获取目标省的边界坐标
    province_boundary = target_province.geometry.iloc[0]
    if province_boundary.geom_type == 'MultiPolygon':
        # 如果是多边形集合，取最大的那个（通常是主要陆地部分）
        province_boundary = max(province_boundary.geoms, key=lambda x: x.area)
    
    # 提取边界坐标点
    boundary_coords = np.array(province_boundary.exterior.coords)
    boundary_lon = boundary_coords[:, 0]
    boundary_lat = boundary_coords[:, 1]
    
    # 读取 ERA5 数据
    dataset = nc.Dataset(file_path)
    lon = dataset.variables['longitude'][:]
    lat = dataset.variables['latitude'][:]
    
    # 提取并转换时间信息
    time_array = extract_time_array(dataset)
    
    # 定义目标经纬度范围（扩展 0.3 度以包含边界）
    lat_range = [min(boundary_lat) - 0.3, max(boundary_lat) + 0.3]
    lon_range = [min(boundary_lon) - 0.3, max(boundary_lon) + 0.3]
    
    # 找到目标经纬度范围的索引
    lat_idx = np.where((lat >= lat_range[0]) & (lat <= lat_range[1]))[0]
    lon_idx = np.where((lon >= lon_range[0]) & (lon <= lon_range[1]))[0]
    
    # 提取目标经纬度范围内的变量数据
    var_subset = dataset.variables[var_name][
        :,  # 时间维度（如果有）
        lat_idx[0]:lat_idx[-1]+1,  # 纬度范围
        lon_idx[0]:lon_idx[-1]+1   # 经度范围
    ]
    
    # 创建经纬度网格
    lon_grid, lat_grid = np.meshgrid(lon[lon_idx], lat[lat_idx])
    
    # 创建用于判断点是否在多边形内的路径
    boundary_path = mpath.Path(np.column_stack([boundary_lon, boundary_lat]))
    
    # 判断每个网格点是否在目标省边界内
    points = np.column_stack([lon_grid.flatten(), lat_grid.flatten()])
    in_province = boundary_path.contains_points(points).reshape(lon_grid.shape)
    
    # 转换为浮点数并将边界外的点设置为 NaN
    in_province = in_province.astype(float)
    in_province[in_province == 0] = np.nan
    
    # 提取目标省的变量数据
    # 注意：根据var_subset的维度调整乘法操作
    if var_subset.ndim == 2:  # 如果没有时间维度
        var_province = var_subset * in_province
    else:  # 如果有时间维度
        # 广播乘法以适应时间维度
        var_province = var_subset * in_province[np.newaxis, :, :]
    
    # 关闭数据集
    dataset.close()
    
    return var_province, lon_grid, lat_grid, time_array

def extract_area_var(file_path, lat_range, lon_range, var_name):
    """
    提取目标区域的变量数据
    
    参数:
        file_path (str): ERA5 数据文件路径（NetCDF 格式）
        lat_range (list): 纬度的上下界范围[lat_min, lat_max]
        lon_range (list): 经度的上下界范围[lon_min, lon_max]
        var_name (str): 目标变量名称（如 'ssr'）
        
    返回:
        tuple: (var_area, lon_grid, lat_grid, time_array)
            - var_area (ndarray): 目标区域的变量数据（矩阵）
            - lon_grid (ndarray): 经度网格
            - lat_grid (ndarray): 纬度网格
            - time_array (array): 标准时间数组
    """
    # 读取 ERA5 数据
    dataset = nc.Dataset(file_path)
    lon = dataset.variables['longitude'][:]  # 读取经度
    lat = dataset.variables['latitude'][:]   # 读取纬度
    
    # 提取并转换时间信息
    time_array = extract_time_array(dataset)
    
    # 找到目标经纬度范围的索引
    lat_idx = np.where((lat >= lat_range[0]) & (lat <= lat_range[1]))[0]
    lon_idx = np.where((lon >= lon_range[0]) & (lon <= lon_range[1]))[0]
    
    # 提取目标经纬度范围内的变量数据
    var_subset = dataset.variables[var_name][
        :,  # 时间维度（如果有）
        lat_idx[0]:lat_idx[-1]+1,  # 纬度范围
        lon_idx[0]:lon_idx[-1]+1   # 经度范围
    ]
    
    # 创建经纬度网格
    lon_grid, lat_grid = np.meshgrid(lon[lon_idx], lat[lat_idx])
    
    # 关闭数据集
    dataset.close()
    
    return var_subset, lon_grid, lat_grid, time_array

def extract_china_var(file_path, shapefile_path, var_name):
    """
    提取全国范围的变量数据
    
    参数:
        file_path (str): ERA5 数据文件路径（NetCDF 格式）
        shapefile_path (str): 国界 Shapefile 文件路径
        var_name (str): 目标变量名称（如 'ssr'）
        
    返回:
        tuple: (var_china, lon_grid, lat_grid, time_array)
            - var_china (ndarray): 全国范围的变量数据（矩阵）
            - lon_grid (ndarray): 经度网格
            - lat_grid (ndarray): 纬度网格
            - time_array (array): 标准时间数组
    """
    # 读取国界数据
    countries = gpd.read_file(shapefile_path)
    
    # 查找中国的边界数据（假设国家名称字段为'country'或'name'）
    # 根据实际shapefile文件的字段名进行调整
    if 'country' in countries.columns:
        target_country = countries[countries['country'] == '中国']
    elif 'name' in countries.columns:
        target_country = countries[countries['name'] == '中国']
    else:
        # 如果没有找到合适的字段，可以尝试使用第一个记录（假设只有中国的数据）
        target_country = countries.iloc[[0]]
    
    if target_country.empty:
        raise ValueError('未找到中国的边界数据')
    
    # 获取中国的边界坐标
    country_boundary = target_country.geometry.iloc[0]
    if country_boundary.geom_type == 'MultiPolygon':
        # 对于多边形集合，我们需要处理所有部分（包括大陆和岛屿）
        # 创建一个空的边界坐标列表
        all_boundary_coords = []
        
        # 遍历所有多边形
        for polygon in country_boundary.geoms:
            # 提取当前多边形的边界坐标
            boundary_coords = np.array(polygon.exterior.coords)
            all_boundary_coords.append(boundary_coords)
        
        # 计算所有边界的经纬度范围
        all_lons = np.concatenate([coords[:, 0] for coords in all_boundary_coords])
        all_lats = np.concatenate([coords[:, 1] for coords in all_boundary_coords])
        
        # 确定整体的经纬度范围
        lon_min, lon_max = np.min(all_lons), np.max(all_lons)
        lat_min, lat_max = np.min(all_lats), np.max(all_lats)
    else:
        # 如果是单个多边形，直接提取边界坐标
        boundary_coords = np.array(country_boundary.exterior.coords)
        lon_min, lon_max = np.min(boundary_coords[:, 0]), np.max(boundary_coords[:, 0])
        lat_min, lat_max = np.min(boundary_coords[:, 1]), np.max(boundary_coords[:, 1])
    
    # 读取 ERA5 数据
    dataset = nc.Dataset(file_path)
    lon = dataset.variables['longitude'][:]
    lat = dataset.variables['latitude'][:]
    
    # 提取并转换时间信息
    time_array = extract_time_array(dataset)
    
    # 定义目标经纬度范围（扩展 0.5 度以包含边界）
    lat_range = [lat_min - 0.5, lat_max + 0.5]
    lon_range = [lon_min - 0.5, lon_max + 0.5]
    
    # 找到目标经纬度范围的索引
    lat_idx = np.where((lat >= lat_range[0]) & (lat <= lat_range[1]))[0]
    lon_idx = np.where((lon >= lon_range[0]) & (lon <= lon_range[1]))[0]
    
    # 提取目标经纬度范围内的变量数据
    var_subset = dataset.variables[var_name][
        :,  # 时间维度（如果有）
        lat_idx[0]:lat_idx[-1]+1,  # 纬度范围
        lon_idx[0]:lon_idx[-1]+1   # 经度范围
    ]
    
    # 创建经纬度网格
    lon_grid, lat_grid = np.meshgrid(lon[lon_idx], lat[lat_idx])
    
    # 创建一个掩码数组，初始化为全False
    in_country = np.zeros(lon_grid.shape, dtype=bool)
    
    # 对于每个多边形（如果是MultiPolygon）
    if country_boundary.geom_type == 'MultiPolygon':
        for polygon in country_boundary.geoms:
            # 提取当前多边形的边界坐标
            boundary_coords = np.array(polygon.exterior.coords)
            boundary_lon = boundary_coords[:, 0]
            boundary_lat = boundary_coords[:, 1]
            
            # 创建用于判断点是否在多边形内的路径
            boundary_path = mpath.Path(np.column_stack([boundary_lon, boundary_lat]))
            
            # 判断每个网格点是否在当前多边形内
            points = np.column_stack([lon_grid.flatten(), lat_grid.flatten()])
            in_polygon = boundary_path.contains_points(points).reshape(lon_grid.shape)
            
            # 更新掩码，如果点在任何一个多边形内，则设为True
            in_country = in_country | in_polygon
    else:
        # 如果是单个多边形
        boundary_lon = boundary_coords[:, 0]
        boundary_lat = boundary_coords[:, 1]
        
        # 创建用于判断点是否在多边形内的路径
        boundary_path = mpath.Path(np.column_stack([boundary_lon, boundary_lat]))
        
        # 判断每个网格点是否在目标国家边界内
        points = np.column_stack([lon_grid.flatten(), lat_grid.flatten()])
        in_country = boundary_path.contains_points(points).reshape(lon_grid.shape)
    
    # 转换为浮点数并将边界外的点设置为 NaN
    in_country = in_country.astype(float)
    in_country[in_country == 0] = np.nan
    
    # 提取目标国家的变量数据
    # 注意：根据var_subset的维度调整乘法操作
    if var_subset.ndim == 2:  # 如果没有时间维度
        var_china = var_subset * in_country
    else:  # 如果有时间维度
        # 广播乘法以适应时间维度
        var_china = var_subset * in_country[np.newaxis, :, :]
    
    # 关闭数据集
    dataset.close()
    
    return var_china, lon_grid, lat_grid, time_array


def extract_area_var_approximately(file_path, province_name, var_name):
    """
    提取目标省份经纬度上下界的变量数据
    
    参数:
        file_path (str): ERA5 数据文件路径（NetCDF 格式）
        province_name (str): 目标省名称（如 '山东省'）
        var_name (str): 目标变量名称（如 'ssr'）
        
    返回:
        tuple: (var_area, lon_grid, lat_grid, time_array)
            - var_area (ndarray): 目标区域的变量数据（矩阵）
            - lon_grid (ndarray): 经度网格
            - lat_grid (ndarray): 纬度网格
            - time_array (array): 标准时间数组
    """
    # 定义各省份的经纬度范围
    province_bounds = {
        # 华北地区
        "北京市": [115.7, 117.4, 39.4, 41.6],  # [经度最小值, 经度最大值, 纬度最小值, 纬度最大值]
        "天津市": [116.7, 118.3, 38.6, 40.2],
        "河北省": [113.5, 119.8, 36.0, 42.5],
        "山西省": [110.2, 114.5, 34.6, 40.7],
        "内蒙古自治区": [97.1, 126.0, 37.4, 53.4],
        
        # 东北地区
        "辽宁省": [118.8, 125.8, 38.7, 43.5],
        "吉林省": [121.6, 131.3, 40.8, 46.3],
        "黑龙江省": [121.2, 135.1, 43.4, 53.3],
        
        # 华东地区
        "上海市": [120.9, 122.1, 30.7, 31.9],
        "江苏省": [116.3, 121.9, 30.8, 35.1],
        "浙江省": [118.0, 123.0, 27.2, 31.5],
        "安徽省": [114.9, 119.7, 29.4, 34.6],
        "福建省": [115.5, 120.5, 23.6, 28.3],
        "江西省": [113.6, 118.5, 24.5, 30.1],
        "山东省": [114.8, 122.7, 34.4, 38.4],
        
        # 中南地区
        "河南省": [110.2, 116.7, 31.4, 36.4],
        "湖北省": [108.4, 116.1, 29.0, 33.3],
        "湖南省": [108.8, 114.2, 24.6, 30.2],
        "广东省": [109.7, 117.3, 20.2, 25.5],
        "广西壮族自治区": [104.5, 112.0, 21.5, 26.4],
        "海南省": [108.6, 111.0, 18.2, 20.2],
        
        # 西南地区
        "重庆市": [105.5, 110.0, 28.2, 32.1],
        "四川省": [97.4, 108.5, 26.0, 34.3],
        "贵州省": [103.6, 109.6, 24.6, 29.2],
        "云南省": [97.5, 106.2, 21.1, 29.3],
        "西藏自治区": [78.4, 99.1, 26.8, 36.5],
        
        # 西北地区
        "陕西省": [105.5, 111.2, 31.7, 39.6],
        "甘肃省": [92.4, 108.7, 32.6, 42.8],
        "青海省": [89.4, 103.0, 31.5, 39.2],
        "宁夏回族自治区": [104.3, 107.7, 35.2, 39.2],
        "新疆维吾尔自治区": [73.5, 96.4, 34.3, 49.5],
        
        # 港澳台地区
        "香港特别行政区": [113.8, 114.5, 22.1, 22.6],
        "澳门特别行政区": [113.5, 113.6, 22.1, 22.2],
        "台湾省": [119.3, 124.5, 21.9, 25.3]
    }
    
    # 检查省份是否存在
    if province_name not in province_bounds:
        raise ValueError(f"未找到省份 '{province_name}' 的经纬度范围数据")
    
    # 获取省份的经纬度范围
    bounds = province_bounds[province_name]
    lon_min, lon_max, lat_min, lat_max = bounds
    
    # 经纬度下界取整再减2，上界向上取整再加2
    lon_min = int(lon_min) - 2
    lat_min = int(lat_min) - 2
    lon_max = int(lon_max + 0.99) + 2  # 向上取整再加2
    lat_max = int(lat_max + 0.99) + 2  # 向上取整再加2
    
    # 调用 extract_area_var 函数提取数据
    lat_range = [lat_min, lat_max]
    lon_range = [lon_min, lon_max]
    
    # 调用 extract_area_var 函数
    var_subset, lon_grid, lat_grid, time_array = extract_area_var(file_path, lat_range, lon_range, var_name)
    
    return var_subset, lon_grid, lat_grid, time_array
