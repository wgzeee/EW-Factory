import sys
import numpy as np

# 添加项目根目录到系统路径
sys.path.append('../')

# 导入项目模块
from src.data_processing import extract_province_var
from src.data_processing import plot_and_save
from src.models import f_solar_power


if __name__ == "__main__":
    file_path = "E:\\data\\era5\\2024\\ssrd_2024.nc"
    shapefile_path = "E:\\电力气象\\地图\\ChinaAdminDivisonSHP-master\\2. Province\\province.shp"
    province_names = ['河北省', '山西省', '辽宁省','吉林省','黑龙江省',
                     '江苏省','浙江省','安徽省','福建省','江西省','山东省','河南省',
                     '湖北省','湖南省','广东省','海南省','四川省','贵州省','云南省',
                     '陕西省','甘肃省','青海省','台湾省','内蒙古自治区','广西壮族自治区',
                     '西藏自治区','宁夏回族自治区','新疆维吾尔自治区','北京市','天津市',
                     '重庆市','上海市']
    var_name = 'ssrd'   
    
    for province_name in province_names:
        # 计算经纬度范围内的太阳辐照强度时间序列均值
        # ssr_mean_series = np.nanmean(var_area, axis=(1, 2))
    
        ssrd_province, lon_grid, lat_grid = extract_province_var.extract_province_var(file_path, shapefile_path, province_name, var_name)  
        # 计算经纬度范围内的太阳辐照强度时间序列均值
        # ssr_mean_series = np.nanmean(var_area, axis=(1, 2))
        
        # 如果是ERA5_land数据，将每日累积量转换为每小时的量
        # if 'land' in file_path:
        #     ssr_mean_series = calculate_hourly_increments.calculate_hourly_increments_1D(ssr_mean_series)
            
        # G = ssrd_province / 3600
        solar_power = f_solar_power.f_solar_power(ssrd_province)
        
        # plot_and_save.plot_and_save_solar_power(solar_power, lon_grid, lat_grid, 
        #                         output_dir="..\\data\\output\\")
            
            
        # 绘制光照强度时间序列图
        import matplotlib.pyplot as plt
        
        # 使用pcolormesh绘制伪彩色网格图（等同于MATLAB的pcolor）
        plt.rcParams['font.sans-serif']=['Microsoft YaHei']  # 用来正常显示中文标签
        # 使用pcolormesh绘制网格图，设置网格线为白色
        pcm = plt.pcolormesh(lon_grid, lat_grid, solar_power[5], cmap='viridis', shading='auto', 
                            edgecolors='white', linewidth=0.5)
        plt.colorbar(pcm)  # 添加颜色条
        plt.title(province_name + '太阳辐照强度分布')
        plt.xlabel('经度')
        plt.ylabel('纬度')
        
        # 显示图形
        plt.show()
        
        
        
        
        
        
        
        
        
        # 创建时间序列
        # hours = np.arange(len(solar_power))
        
        # # 创建图形
        # plt.figure(figsize=(12, 6))
        # plt.plot(hours, solar_power, 'b-', linewidth=1)
        
        # # 设置图形标题和轴标签
        # plt.title('每小时太阳辐照强度变化')
        # plt.xlabel('小时')
        # plt.ylabel('太阳辐照强度 (W/m²)')
        
        # # 添加网格
        # plt.grid(True, linestyle='--', alpha=0.7)
        
        # # 显示图形
        # plt.show()