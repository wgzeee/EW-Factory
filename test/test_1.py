import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import netCDF4 as nc

# 添加项目根目录到系统路径
sys.path.append('../')

# 导入项目模块
from src.data_processing import extract_var
from src.data_processing import calculate_hourly_increments
from src.data_processing import energy_statistics
from src.models import f_solar_power
from src.data_processing import png_and_gif
from src.data_processing import custom_plot 
from src.data_processing import aggregate_power_output 



if __name__ == "__main__":
    '''
    file_path = "D:\\data\\era5\\2024\\ERA5_hourily_ssr_2024.nc"
    shapefile_path = "D:\\研究课题\\15-电力气象\\地图\\ChinaAdminDivisonSHP-master\\2. Province\\province.shp"
    # province_names = ['河北省', '山西省', '辽宁省','吉林省','黑龙江省',
    #                  '江苏省','浙江省','安徽省','福建省','江西省','山东省','河南省',
    #                  '湖北省','湖南省','广东省','海南省','四川省','贵州省','云南省',
    #                  '陕西省','甘肃省','青海省','台湾省','内蒙古自治区','广西壮族自治区',
    #                  '西藏自治区','宁夏回族自治区','新疆维吾尔自治区','北京市','天津市',
    #                  '重庆市','上海市']
    province_names = ['山东省']
    var_name = 'ssr'   
    
    for province_name in province_names:
        ssrd_province, lon_grid, lat_grid, time_array = extract_var.extract_province_var(file_path, shapefile_path, province_name, var_name)  
        # 计算经纬度范围内的太阳辐照强度时间序列均值
        # ssr_mean_series = np.nanmean(var_area, axis=(1, 2))
        
        # 如果是ERA5_land数据，将每日累积量转换为每小时的量
        # if 'land' in file_path:
        #     ssr_mean_series = calculate_hourly_increments.calculate_hourly_increments_1D(ssr_mean_series)
            
        # G = ssrd_province / 3600
        solar_power = f_solar_power.f_solar_power_2(ssrd_province)
        daily_energys, monthly_energys, annual_energys = energy_statistics.calculate_energy_statistics(solar_power, time_array)

        # # 绘制图像并保存为GIF
        # save_dir = 'D:\\output\\solar_power\\山东省'
        # image_path = png_and_gif.save_png(solar_power[0:24], lon_grid, lat_grid, output_dir=save_dir, bar_type='minmax')
        # png_and_gif.generate_gif(image_path, save_dir, dur=250)
        
        # custom_plot.plot_monthly_boxplot(monthly_energys, province_name)
        # custom_plot.plot_monthly_comparison(monthly_energys, province_name)
        # custom_plot.plot_monthly_violin(monthly_energys, province_name)
        # custom_plot.plot_calendar_heatmap(daily_energys, time_array, province_name)

    
    
        # image_path = []
        # for i in range(24):
        #     # 创建固定大小的图形
        #     fig = plt.figure(figsize=(10, 8), dpi=100)  # 固定图形大小和DPI
            
        #     # 使用pcolormesh绘制伪彩色网格图
        #     plt.rcParams['font.sans-serif']=['Microsoft YaHei']
        #     pcm = plt.pcolormesh(lon_grid, lat_grid, solar_power[i], cmap='viridis', shading='auto', 
        #                         edgecolors='white', linewidth=0.5)
        #     plt.colorbar(pcm)  # 添加颜色条
        #     pcm.set_clim(vmin=0, vmax=0.6)
        #     # pcm.set_clim(vmin=np.nanmin(solar_power[i]), vmax=np.nanmax(solar_power[i]))
        #     plt.title(f'太阳能逐小时容量系数 ({time_array[i].strftime("%Y年%m月%d日 %H时")} UTC) {province_name}')
        #     # plt.title(f'太阳能逐月电量 (2024年1月{i+1}日) {province_name}')
        #     plt.xlabel('经度')
        #     plt.ylabel('纬度')
            
        #     # 设置固定的坐标轴范围
        #     plt.xlim([np.min(lon_grid), np.max(lon_grid)])
        #     plt.ylim([np.min(lat_grid), np.max(lat_grid)])
            
        #     # 保存图像时使用固定的尺寸
        #     save_dir = f"D:\\output\\solar_power\\{province_name}"
        #     if not os.path.exists(save_dir):
        #         os.makedirs(save_dir)
            
        #     save_path = os.path.join(save_dir, f"太阳能逐小时电量 (2024年1月1日{i}时) {province_name}.png")
        #     plt.savefig(save_path, dpi=100, bbox_inches=None)  # 不使用bbox_inches='tight'，保持固定尺寸
            
        #     plt.close(fig)
        #     image_path.append(save_path)
        # '''

        

    file_path = "G:\\ERA5\\surface_solar_radiation_downwards"
    shapefile_path = "D:\\wgzee\\Documents\\GitHub\\EW-Factory\\data\\地图\\province.shp"
    var_name = 'ssrd'
    csv_file_path = "D:\\wgzee\\Documents\\GitHub\\EW-Factory\\data\\装机\\China_solar_power_2025.2.csv"
    province_name = "山东省"   
    
    # 提取全球ERA5的数据
    # file_path = "G:\\ERA5\\surface_solar_radiation_downwards\\era5_surface_solar_radiation_downwards_2024_12.nc"
    # dataset = nc.Dataset(file_path)
    # lon = dataset.variables['longitude'][:]
    # lat = dataset.variables['latitude'][:]
    # lon_grid, lat_grid = np.meshgrid(lon, lat)
    # time_array = extract_var.extract_time_array(dataset)
    # ssrd_province = dataset.variables[var_name][:]
    
    ssrd_province, lon_grid, lat_grid, time_array = extract_var.extract_annual_data(file_path, 2019, 'approximate', province_name, shapefile_path)  
    temperature, lon_grid, lat_grid, time_array = extract_var.extract_annual_data("G:\\ERA5\\2m_temperature", 2019, 'approximate', province_name, shapefile_path, var_name='t2m')  
        
    # ssrd_country, lon_grid, lat_grid, time_array = extract_var.extract_china_var(file_path, shapefile_path, var_name)  
    # solar_power = f_solar_power.f_solar_power_2(ssrd_country)
    
    plt.figure(figsize=(10, 8), dpi=300)  # 固定图形大小和DPI
    plt.rcParams['font.sans-serif']=['Microsoft YaHei']
    pcm = plt.pcolormesh(lon_grid, lat_grid, ssrd_province[5], cmap='viridis', shading='auto', 
                        edgecolors='white', linewidth=0)
    plt.colorbar(pcm)  # 添加颜色条
    # pcm.set_clim(vmin=0, vmax=0.6)
    pcm.set_clim(vmin=np.nanmin(ssrd_province[5]), vmax=np.nanmax(ssrd_province[5]))
    # plt.title(f'太阳能逐小时容量系数 ({time_array[i].strftime("%Y年%m月%d日 %H时")} UTC) {province_name}')
    # plt.title(f'太阳能逐月电量 (2024年1月{i+1}日) {province_name}')
    plt.xlabel('经度')
    plt.ylabel('纬度')
    plt.show()
    ssrd_province = calculate_hourly_increments.calculate_hourly_increments_3D(ssrd_province)
    total_power_output = aggregate_power_output.calculate_province_power_output(ssrd_province, lon_grid, lat_grid, csv_file_path, province_name)
    # 绘制总出力折线图
    plt.rcParams['font.sans-serif']=['Microsoft YaHei']
    plt.figure(figsize=(12, 6))
    plt.plot(range(len(time_array)), np.array(total_power_output), 'b-', linewidth=1.5)
    plt.title(f'{province_name}太阳能总出力情况')
    plt.xlabel('时间')
    plt.ylabel('总出力 (归一化)')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 设置x轴日期格式
    plt.gcf().autofmt_xdate()  # 自动格式化x轴日期标签
    
    # 添加数据范围信息
    plt.figtext(0.02, 0.02, f'数据范围: {time_array[0].strftime("%Y-%m-%d")} 至 {time_array[-1].strftime("%Y-%m-%d")}', 
                fontsize=9, color='gray')
    plt.show()

