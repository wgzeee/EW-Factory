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

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    file_path = "E:\\data\\era5\\2024\\ssrd_2024.nc"
    shapefile_path = "E:\\电力气象\\地图\\ChinaAdminDivisonSHP-master\\2. Province\\province.shp"
    province_name = '山东省'
    var_name = 'ssrd'
    
    ssrd_province, lon_grid, lat_grid, time_array = extract_province_var(file_path, shapefile_path, province_name, var_name)  
    contour = plt.contourf(lon_grid, lat_grid, ssrd_province[1], cmap='viridis')  # 使用 contourf 绘制等值图
    plt.colorbar(contour)  # 添加颜色条  
    plt.show()  # 添加这行来显示图形