import numpy as np

def calculate_hourly_increments_1D(G_cumulative):
    """
    计算每小时的光照强度增量
    
    参数:
        G_cumulative (ndarray): 一维数组，表示累加的光照强度数据
        
    返回:
        ndarray: 一维数组，表示每小时的光照强度增量（单位：W/m²）
    """
    # 检查输入参数
    hours_per_day = 24
    if len(G_cumulative) % hours_per_day != 0:
        raise ValueError('数据长度必须是每天小时数的整数倍')
    
    # 初始化输出数组
    num_days = len(G_cumulative) // hours_per_day  # 计算天数
    G_incremental = np.zeros_like(G_cumulative)    # 初始化增量数组
    
    # 处理数据
    G_processed = np.copy(G_cumulative)
    G_processed = np.delete(G_processed, 0)  # 删除第一个元素
    G_processed = np.append(G_processed, G_processed[-1])  # 末尾添加最后一个元素
    
    # 逐天计算每小时增量
    for day in range(1, num_days + 1):
        # 获取当天的数据
        start_idx = (day - 1) * hours_per_day + 1  # 当天起始索引
        end_idx = day * hours_per_day              # 当天结束索引
        daily_data = G_processed[start_idx-1:end_idx]  # 当天数据
        
        # 计算每小时增量
        daily_increments = np.diff(daily_data)  # 计算增量
        daily_increments = np.insert(daily_increments, 0, daily_data[0])  # 保留第一小时数据
        
        # 将结果存入输出数组
        G_incremental[start_idx-1:end_idx] = daily_increments
    
    # 调整首尾
    G_incremental = np.insert(G_incremental, 0, G_incremental[23])
    G_incremental = G_incremental[:-1]
    
    return G_incremental

def calculate_hourly_increments_3D(G_cumulative):
    """
    计算每小时的光照强度增量，支持三维输入（lat x lon x time）
    
    参数:
        G_cumulative (ndarray): 三维数组，前两维是空间维度，第三维是时间
        
    返回:
        ndarray: 三维数组，每小时的光照强度增量
    """
    # 参数设置
    hours_per_day = 24
    lat, lon, num_time = G_cumulative.shape
    
    # 检查时间维度是否为24的整数倍
    if num_time % hours_per_day != 0:
        raise ValueError('时间维的长度必须是24的整数倍')
    
    # 预处理：删除第一个时间点，末尾添加最后一个时间点
    G_processed = G_cumulative[:, :, 1:]  # 删除第三维第一个元素
    G_processed = np.concatenate((G_processed, G_processed[:, :, -1:]), axis=2)  # 末尾复制最后一个元素
    
    # 初始化输出数组
    num_days = num_time // hours_per_day
    G_incremental = np.zeros((lat, lon, num_time))
    
    # 逐天计算增量
    for day in range(1, num_days + 1):
        # 获取当天处理后的数据块
        start_idx = (day - 1) * hours_per_day
        end_idx = day * hours_per_day
        daily_data = G_processed[:, :, start_idx:end_idx]  # lat x lon x 24
        
        # 计算差分并补首值
        daily_diff = np.diff(daily_data, axis=2)  # 沿时间维差分
        daily_increments = np.concatenate((daily_data[:, :, 0:1], daily_diff), axis=2)  # 拼接首值
        
        # 存储结果
        G_incremental[:, :, start_idx:end_idx] = daily_increments
    
    # 调整首尾数据
    G_incremental = np.concatenate((G_incremental[:, :, 23:24], G_incremental), axis=2)  # 首部插入第24小时
    G_incremental = G_incremental[:, :, :-1]  # 删除末尾元素
    
    return G_incremental

if __name__ == "__main__":
    import extract_area_var
    file_path = "E:\\data\\ERA5_land_hourily_ssrd_202401.nc"
    lat_range = [34.0, 38.0]  # 纬度范围
    lon_range = [115.0, 122.0]  # 经度范围
    var_name = 'ssrd'   
    
    var_area, lon_grid, lat_grid = extract_area_var.extract_area_var(file_path, lat_range, lon_range, var_name) 
    # 计算经纬度范围内的太阳辐照强度时间序列均值
    ssr_mean_series = np.nanmean(var_area, axis=(1, 2))
    
    # 如果是ERA5_land数据，将每日累积量转换为每小时的量
    if 'land' in file_path:
        ssr_mean_series = calculate_hourly_increments_1D(ssr_mean_series)
        
    # 绘制光照强度时间序列图
    import matplotlib.pyplot as plt
    
    # 创建时间序列
    hours = np.arange(len(ssr_mean_series))
    
    # 创建图形
    plt.figure(figsize=(12, 6))
    plt.plot(hours, ssr_mean_series, 'b-', linewidth=1)
    
    # 设置图形标题和轴标签
    plt.title('每小时太阳辐照强度变化')
    plt.xlabel('小时')
    plt.ylabel('太阳辐照强度 (W/m²)')
    
    # 添加网格
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 显示图形
    plt.show()
