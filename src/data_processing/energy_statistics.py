import numpy as np
import matplotlib.pyplot as plt
import os
import calendar
from datetime import datetime

def calculate_energy_statistics(power_data, time_array, stat_type='all'):
    """
    计算网格化出力数据的每日、每月和全年电量统计
    
    参数:
        power_data (ndarray): 形状为(时间, 纬度, 经度)的出力数据，单位为kW或W
        time_array (array): 时间数组，包含每个时间步的日期时间信息
        stat_type (str): 统计类型，可选值为'daily'、'monthly'、'annual'或'all'
        
    返回:
        根据stat_type返回相应的统计结果:
            - 'daily': 形状为(天数, 纬度, 经度)的每日电量统计
            - 'monthly': 形状为(12, 纬度, 经度)的每月电量统计
            - 'annual': 形状为(纬度, 经度)的全年电量统计
            - 'all': 返回(daily_energy, monthly_energy, annual_energy)元组
    """
    # 获取数据维度
    time_steps, lat_size, lon_size = power_data.shape
    
    # 提取时间信息
    days = np.array([t.day for t in time_array])
    months = np.array([t.month for t in time_array])
    years = np.array([t.year for t in time_array])
    
    # 根据统计类型选择性计算
    if stat_type in ['daily', 'all']:
        # 获取年份和判断是否为闰年
        year = years[0]
        is_leap_year = calendar.isleap(year)
        days_in_year = 366 if is_leap_year else 365
        
        # 初始化每日电量数组
        daily_energy = np.zeros((days_in_year, lat_size, lon_size))
        
        # 创建日期索引映射
        date_to_idx = {}
        for i in range(time_steps):
            date = datetime(years[i], months[i], days[i]).strftime('%Y-%m-%d')
            if date not in date_to_idx:
                day_of_year = (datetime(years[i], months[i], days[i]) - datetime(years[i], 1, 1)).days
                date_to_idx[date] = day_of_year
        
        # 按日期累加电量
        for i in range(time_steps):
            date = datetime(years[i], months[i], days[i]).strftime('%Y-%m-%d')
            day_idx = date_to_idx[date]
            daily_energy[day_idx] += power_data[i]
    
    if stat_type in ['monthly', 'all']:
        # 初始化每月电量数组
        monthly_energy = np.zeros((12, lat_size, lon_size))
        
        # 计算每月电量
        for month in range(1, 13):
            month_mask = months == month
            monthly_energy[month-1] = np.sum(power_data[month_mask], axis=0)
    
    if stat_type in ['annual', 'all']:
        # 计算全年电量
        annual_energy = np.sum(power_data, axis=0)
    
    # 根据统计类型返回结果
    if stat_type == 'daily':
        return daily_energy
    elif stat_type == 'monthly':
        return monthly_energy
    elif stat_type == 'annual':
        return annual_energy
    else:  # 'all'
        return daily_energy, monthly_energy, annual_energy

def plot_energy_map(energy_data, lon_grid, lat_grid, title, output_path=None):
    """
    绘制电量分布图
    
    参数:
        energy_data (ndarray): 形状为(纬度, 经度)的电量数据
        lon_grid (ndarray): 经度网格
        lat_grid (ndarray): 纬度网格
        title (str): 图表标题
        output_path (str, optional): 输出文件路径，如果为None则显示图形
    """
    plt.figure(figsize=(10, 8))
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 用来正常显示中文标签
    
    # 使用pcolormesh绘制网格图
    pcm = plt.pcolormesh(lon_grid, lat_grid, energy_data, cmap='viridis', shading='auto')
    plt.colorbar(pcm, label='电量 (Wh 或 kWh)')
    plt.title(title)
    plt.xlabel('经度')
    plt.ylabel('纬度')
    plt.grid(True, linestyle='--', alpha=0.3)
    
    if output_path:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    else:
        plt.show()