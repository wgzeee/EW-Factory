import numpy as np
import netCDF4 as nc
import geopandas as gpd
from shapely.geometry import Point, Polygon
import matplotlib.path as mpath

def extract_province_var(file_path, shapefile_path, province_name, var_name):
    """
    提取目标省的变量数据
    
    参数:
        file_path (str): ERA5 数据文件路径（NetCDF 格式）
        shapefile_path (str): 省界 Shapefile 文件路径
        province_name (str): 目标省名称（如 '山东省'）
        var_name (str): 目标变量名称（如 'ssr'）
        
    返回:
        tuple: (var_province, lon_grid, lat_grid)
            - var_province (ndarray): 目标省的变量数据（矩阵）
            - lon_grid (ndarray): 经度网格
            - lat_grid (ndarray): 纬度网格
    """
    # 读取省界数据
    provinces = gpd.read_file(shapefile_path)
    
    # 查找目标省的边界数据
    target_province = provinces[provinces['NAME'] == province_name]
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
    
    return var_province, lon_grid, lat_grid

if __name__ == "__main__":
    file_path = "D:/ERA5/2022/ssr/ssr_2022.nc"
    shapefile_path = "E:\\电力气象\\地图\\ChinaAdminDivisonSHP-master\\2. Province\\province.shp"
    province_name = '山东省'
    var_name = 'ssr'
    
    provinces = gpd.read_file(shapefile_path)
    print("数据类型:", type(provinces))
    print("\n数据形状:", provinces.shape)
    print("\n列名:", provinces.columns.tolist())