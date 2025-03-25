import sys
import numpy as np

# 添加项目根目录到系统路径
sys.path.append('../')

# 导入项目模块
from src.data_processing import extract_area_var
from src.data_processing import calculate_hourly_increments
from src.models import f_solar_power


if __name__ == "__main__":
    file_path = "E:\\data\\ERA5_land_hourily_ssrd_202401.nc"
    lat_range = [35.0, 38.0]  # 纬度范围
    lon_range = [115.0, 123.0]  # 经度范围
    var_name = 'ssrd'   
    
    var_area, lon_grid, lat_grid = extract_area_var.extract_area_var(file_path, lat_range, lon_range, var_name) 
    # 计算经纬度范围内的太阳辐照强度时间序列均值
    ssr_mean_series = np.nanmean(var_area, axis=(1, 2))
    
    # 如果是ERA5_land数据，将每日累积量转换为每小时的量
    if 'land' in file_path:
        ssr_mean_series = calculate_hourly_increments.calculate_hourly_increments_1D(ssr_mean_series)
        
    G = ssr_mean_series / 3600
    solar_power = f_solar_power.f_solar_power(G)
        
        
    # 绘制光照强度时间序列图
    import matplotlib.pyplot as plt
    
    # 创建时间序列
    hours = np.arange(len(solar_power))
    
    # 创建图形
    plt.figure(figsize=(12, 6))
    plt.plot(hours, solar_power, 'b-', linewidth=1)
    
    # 设置图形标题和轴标签
    plt.title('每小时太阳辐照强度变化')
    plt.xlabel('小时')
    plt.ylabel('太阳辐照强度 (W/m²)')
    
    # 添加网格
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 显示图形
    plt.show()