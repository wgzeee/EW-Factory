import numpy as np
import netCDF4 as nc

def extract_area_var(file_path, lat_range, lon_range, var_name):
    """
    提取目标区域的变量数据
    
    参数:
        file_path (str): ERA5 数据文件路径（NetCDF 格式）
        lat_range (list): 纬度的上下界范围[lat_min, lat_max]
        lon_range (list): 经度的上下界范围[lon_min, lon_max]
        var_name (str): 目标变量名称（如 'ssr'）
        
    返回:
        tuple: (var_area, lon_grid, lat_grid)
            - var_area (ndarray): 目标区域的变量数据（矩阵）
            - lon_grid (ndarray): 经度网格
            - lat_grid (ndarray): 纬度网格
    """
    # 读取 ERA5 数据
    dataset = nc.Dataset(file_path)
    lon = dataset.variables['longitude'][:]  # 读取经度
    lat = dataset.variables['latitude'][:]   # 读取纬度
    
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
    
    return var_subset, lon_grid, lat_grid

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    # 示例用法
    file_path = "E:\\data\\era5\\2024\\ssrd_2024.nc"
    lat_range = [34.0, 38.0]  # 纬度范围
    lon_range = [115.0, 122.0]  # 经度范围
    var_name = 'ssrd'
    
    var_area, lon_grid, lat_grid = extract_area_var(file_path, lat_range, lon_range, var_name)
    contour = plt.contourf(lon_grid, lat_grid, var_area[1], cmap='viridis')  # 使用 contourf 绘制等值图
    plt.colorbar(contour)  # 添加颜色条  
    plt.show()  # 添加这行来显示图形