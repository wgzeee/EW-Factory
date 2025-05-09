import pandas as pd
import numpy as np
from datetime import datetime
import os
import re
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, DayLocator, HourLocator
import matplotlib.dates as mdates

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

def get_energy_type_and_location(filename):
    """根据文件名确定能源类型和地点"""
    filename = os.path.basename(filename)
    energy_type = "光伏" if "solar" in filename.lower() else "风电"
    # 提取中文部分作为地点
    location = re.findall(r'[\u4e00-\u9fa5]+', filename)[0]
    return energy_type, location

def calculate_data_index(date_str):
    """计算给定日期对应的数据索引"""
    date = datetime.strptime(date_str, '%Y-%m-%d')
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if date.year % 4 == 0 and (date.year % 100 != 0 or date.year % 400 == 0):
        days_in_month[1] = 29
    
    total_days = sum(days_in_month[:date.month-1]) + date.day
    return (total_days - 1) * 24

def analyze_low_power_periods(data, start_idx, end_idx, energy_type):
    """分析低出力天气期间"""
    # 提取指定时间段的数据
    period_data = data[start_idx:end_idx]
    
    # 计算每24小时的平均值
    daily_means = []
    for i in range(0, len(period_data), 24):
        daily_data = period_data[i:i+24]
        if energy_type == "光伏":
            # 对于光伏数据，只考虑大于等于0.001的值（白天数据）
            daytime_data = daily_data[daily_data >= 0.001]
            daily_mean = np.mean(daytime_data) if len(daytime_data) > 0 else 0
        else:
            # 对于风电数据，考虑所有数据
            daily_mean = np.mean(daily_data)
        daily_means.append(daily_mean)
    
    # 找出所有低出力天气（平均值<=0.1）
    low_power_periods = []
    current_period = []
    
    for i, mean in enumerate(daily_means):
        if mean <=0.1:
            current_period.append(i)
        elif current_period:
            if len(current_period) >= 3:  # 持续时间超过3天
                low_power_periods.append(current_period.copy())
            current_period = []
    
    # 处理最后一个时间段
    if current_period and len(current_period) >= 3:
        low_power_periods.append(current_period)
    
    # 按持续时间降序排序
    low_power_periods.sort(key=len, reverse=True)
    
    return low_power_periods

def calculate_weighted_average(data, start_idx, period, energy_type):
    """计算低出力期间的加权平均值"""
    period_start_idx = start_idx + period[0] * 24
    period_end_idx = start_idx + (period[-1] + 1) * 24
    period_data = data[period_start_idx:period_end_idx]
    
    if energy_type == "光伏":
        # 对于光伏数据，只考虑大于等于0.001的值（白天数据）
        daytime_data = period_data[period_data >= 0.001]
        return np.mean(daytime_data) if len(daytime_data) > 0 else 0
    else:
        # 对于风电数据，考虑所有数据
        return np.mean(period_data)

def plot_low_power_scenarios(data, start_idx, end_idx, low_power_periods, start_date, min_duration, energy_type):
    """绘制低出力场景图"""
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    
    # 筛选持续时间大于等于指定天数的场景
    filtered_periods = [period for period in low_power_periods if len(period) >= min_duration]
    
    if not filtered_periods:
        print(f"未找到持续时间大于等于{min_duration}天的低出力场景")
        return
    
    # 为每个场景创建子图
    fig, axes = plt.subplots(len(filtered_periods), 1, figsize=(15, 4*len(filtered_periods)))
    if len(filtered_periods) == 1:
        axes = [axes]
    
    for idx, period in enumerate(filtered_periods):
        # 计算场景的时间范围
        period_start_idx = start_idx + period[0] * 24
        period_end_idx = start_idx + (period[-1] + 1) * 24
        
        # 提取场景数据
        scenario_data = data[period_start_idx:period_end_idx]
        
        # 创建时间序列
        start_time = start_date_obj + pd.Timedelta(days=period[0])
        time_series = pd.date_range(start=start_time, periods=len(scenario_data), freq='H')
        
        # 绘制数据（移除平均值线）
        axes[idx].plot(time_series, scenario_data, 'b-', linewidth=1.5, label='出力值')
        
        # 设置图表格式
        axes[idx].set_title(f'低出力场景 {idx+1} (持续时间: {len(period)}天)', fontsize=14, pad=15)
        axes[idx].set_xlabel('时间', fontsize=12)
        axes[idx].set_ylabel('出力值', fontsize=12)
        axes[idx].grid(True, linestyle='--', alpha=0.7)
        axes[idx].legend(loc='upper right', fontsize=11)
        
        # 设置x轴刻度
        axes[idx].xaxis.set_major_locator(DayLocator())
        axes[idx].xaxis.set_minor_locator(HourLocator(interval=6))
        axes[idx].xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
        
        # 设置y轴范围统一为0到1
        axes[idx].set_ylim(0, 1)
        
        # 设置刻度标签字体大小
        axes[idx].tick_params(axis='both', labelsize=10)
    
    plt.tight_layout()
    return fig

def plot_monthly_power(data, start_date_obj, energy_type, location):
    """绘制月度总出力图"""
    # 创建新的图表
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 计算每月的总出力
    monthly_power = []
    month_names = []
    
    # 计算每月的起始索引
    month_starts = [0]  # 第一个月从0开始
    days_sum = 0
    for month in range(1, 12):  # 只需要计算到11月
        days_in_month = pd.Period(f'{start_date_obj.year}-{month}').days_in_month
        days_sum += days_in_month
        month_starts.append(days_sum * 24)
    
    # 处理所有月份的数据
    for month in range(1, 13):
        month_start = month_starts[month-1]
        if month < 12:
            month_end = month_starts[month]
        else:
            month_end = len(data)  # 对于12月，使用数据的总长度作为结束索引
        
        # 提取当月数据并计算总和
        month_data = data[month_start:month_end]
        monthly_power.append(np.sum(month_data))
        month_names.append(f'{month}月')
    
    # 绘制柱状图
    bars = ax.bar(month_names, monthly_power, color='skyblue')
    
    # 在柱子上添加数值标签
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom',
                fontsize=11)
    
    # 设置图表格式
    ax.set_title(f'{start_date_obj.year}年{location}{energy_type}月度总出力', fontsize=20, pad=21)
    ax.set_xlabel('月份', fontsize=18)
    ax.set_ylabel('总出力', fontsize=18)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # 设置刻度标签字体大小
    ax.tick_params(axis='both', labelsize=14)
    
    plt.tight_layout()
    return fig

def plot_random_august_period(data, start_date_obj, energy_type, location):
    """随机绘制8月份连续11天的出力曲线图"""
    # 计算8月1日的起始索引
    days_before_august = sum([31, 28, 31, 30, 31, 30, 31])  # 1-7月的天数
    if start_date_obj.year % 4 == 0 and (start_date_obj.year % 100 != 0 or start_date_obj.year % 400 == 0):
        days_before_august += 1  # 闰年调整
    
    august_start_idx = days_before_august * 24
    august_end_idx = (days_before_august + 31) * 24  # 8月结束索引
    
    # 计算可选的起始日期范围（确保有11天的数据）
    max_start_day = 21  # 31 - 11 + 1
    random_day = np.random.randint(1, max_start_day + 1)
    
    # 计算选中时间段的起始和结束索引
    period_start_idx = august_start_idx + (random_day - 1) * 24
    period_end_idx = period_start_idx + 11 * 24
    
    # 提取数据
    period_data = data[period_start_idx:period_end_idx]
    
    # 创建时间序列
    start_time = datetime(start_date_obj.year, 8, random_day)
    time_series = pd.date_range(start=start_time, periods=len(period_data), freq='H')
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(15, 6))
    
    # 绘制数据（移除平均值线）
    ax.plot(time_series, period_data, 'b-', linewidth=1.5, label='出力值')
    
    # 设置图表格式
    ax.set_title(f'{start_date_obj.year}年{location}{energy_type}出力曲线\n'
                 f'(8月{random_day}日-{random_day+10}日)', 
                 fontsize=14, pad=15)
    ax.set_xlabel('时间', fontsize=12)
    ax.set_ylabel('出力值', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(loc='upper right', fontsize=11)
    
    # 设置x轴刻度
    ax.xaxis.set_major_locator(DayLocator())
    ax.xaxis.set_minor_locator(HourLocator(interval=6))
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    
    # 设置y轴范围
    ax.set_ylim(0, 1)
    
    # 设置刻度标签字体大小
    ax.tick_params(axis='both', labelsize=10)
    
    plt.tight_layout()
    return fig

def analyze_high_power_periods(data, start_idx, end_idx, energy_type, threshold=0.8):
    """分析高出力天气期间"""
    # 提取指定时间段的数据
    period_data = data[start_idx:end_idx]
    
    # 第一步：计算每日平均出力
    daily_means = []
    for i in range(0, len(period_data), 24):
        daily_data = period_data[i:i+24]
        if energy_type == "光伏":
            # 对于光伏数据，只考虑大于等于0.001的值（白天数据）
            daytime_data = daily_data[daily_data >= 0.001]
            daily_mean = np.mean(daytime_data) if len(daytime_data) > 0 else 0
        else:
            # 对于风电数据，考虑所有数据
            daily_mean = np.mean(daily_data)
        daily_means.append(daily_mean)
    
    # 第二步：寻找高出力场景
    high_power_periods = []
    
    # 遍历每一天作为起始日
    for start_day in range(len(daily_means)):
        current_period = []
        cumulative_sum = 0
        
        # 从start_day开始累加检查
        for day in range(start_day, len(daily_means)):
            cumulative_sum += daily_means[day]
            period_mean = cumulative_sum / (day - start_day + 1)
            
            # 如果平均值大于阈值，继续累加
            if period_mean >= threshold:
                current_period = list(range(start_day, day + 1))
            else:
                break
        
        # 如果找到符合条件的时间段且长度大于等于3天，保存该时间段
        if len(current_period) >= 3:
            high_power_periods.append(current_period)
    
    # 移除被其他更长时段完全包含的时段
    filtered_periods = []
    for period in sorted(high_power_periods, key=len, reverse=True):
        period_set = set(period)
        # 检查这个时段是否被任何已保存的更长时段包含
        if not any(period_set.issubset(set(saved_period)) for saved_period in filtered_periods):
            filtered_periods.append(period)
    
    # 按持续时间降序排序
    filtered_periods.sort(key=len, reverse=True)
    
    return filtered_periods

def plot_high_power_scenarios(data, start_idx, end_idx, high_power_periods, start_date, min_duration, energy_type, threshold):
    """绘制高出力场景图"""
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    
    # 筛选持续时间大于等于指定天数的场景
    filtered_periods = [period for period in high_power_periods if len(period) >= min_duration]
    
    if not filtered_periods:
        print(f"未找到持续时间大于等于{min_duration}天的高出力场景")
        return
    
    # 为每个场景创建子图
    fig, axes = plt.subplots(len(filtered_periods), 1, figsize=(15, 4*len(filtered_periods)))
    if len(filtered_periods) == 1:
        axes = [axes]
    
    for idx, period in enumerate(filtered_periods):
        # 计算场景的时间范围
        period_start_idx = start_idx + period[0] * 24
        period_end_idx = start_idx + (period[-1] + 1) * 24
        
        # 提取场景数据
        scenario_data = data[period_start_idx:period_end_idx]
        
        # 创建时间序列
        start_time = start_date_obj + pd.Timedelta(days=period[0])
        time_series = pd.date_range(start=start_time, periods=len(scenario_data), freq='H')
        
        # 绘制数据
        axes[idx].plot(time_series, scenario_data, 'r-', linewidth=1.5, label='出力值')
        
        # 设置图表格式
        axes[idx].set_title(f'高出力场景 {idx+1} (持续时间: {len(period)}天)', fontsize=14, pad=15)
        axes[idx].set_xlabel('时间', fontsize=12)
        axes[idx].set_ylabel('出力值', fontsize=12)
        axes[idx].grid(True, linestyle='--', alpha=0.7)
        axes[idx].legend(loc='upper right', fontsize=11)
        
        # 设置x轴刻度
        axes[idx].xaxis.set_major_locator(DayLocator())
        axes[idx].xaxis.set_minor_locator(HourLocator(interval=6))
        axes[idx].xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
        
        # 设置y轴范围统一为0到1
        axes[idx].set_ylim(0, 1)
        
        # 设置刻度标签字体大小
        axes[idx].tick_params(axis='both', labelsize=10)
    
    plt.tight_layout()
    return fig

def main():
    try:
        # 获取当前文件夹路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 获取用户输入的CSV文件名
        csv_name = input("请输入CSV文件名（例如：solar_北京.csv）: ")
        file_path = os.path.join(current_dir, csv_name)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"错误：在当前文件夹中未找到文件 {csv_name}")
            return
            
        # 获取日期输入
        start_date = input("请输入起始日期 (YYYY-MM-DD): ")
        end_date = input("请输入结束日期 (YYYY-MM-DD): ")
        
        # 创建start_date_obj（移到这里）
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        
        # 读取CSV文件
        df = pd.read_csv(file_path)
        data = df.iloc[:, 0].values  # 假设第一列为出力数据
        
        # 计算数据索引
        start_idx = calculate_data_index(start_date)
        end_idx = calculate_data_index(end_date)
        
        # 获取能源类型和地点
        energy_type, location = get_energy_type_and_location(file_path)
        
        # 获取最小持续时间参数
        while True:
            try:
                min_duration = int(input("请输入最小持续时间（天）: "))
                if min_duration > 0:
                    break
                print("请输入大于0的数字")
            except ValueError:
                print("请输入有效的数字")
        
        # 获取高出力阈值参数（可选）
        high_power_threshold = input("请输入高出力阈值（直接回车则使用默认值0.8）: ").strip()
        high_power_threshold = float(high_power_threshold) if high_power_threshold else 0.8
        
        # 分析低出力期间
        low_power_periods = analyze_low_power_periods(data, start_idx, end_idx, energy_type)
        
        # 绘制场景图
        fig = plot_low_power_scenarios(data, start_idx, end_idx, low_power_periods, 
                                     start_date, min_duration, energy_type)
        
        # 保存场景图
        if fig:
            plot_filename = f"{start_date_obj.year}_{energy_type}_{location}_scenarios.png"
            fig.savefig(plot_filename, dpi=300, bbox_inches='tight')
            print(f"场景图已保存到: {plot_filename}")
        
        # 绘制月度总出力图
        monthly_fig = plot_monthly_power(data, start_date_obj, energy_type, location)
        
        # 保存月度总出力图
        if monthly_fig:
            monthly_plot_filename = f"{start_date_obj.year}_{energy_type}_{location}_monthly.png"
            monthly_fig.savefig(monthly_plot_filename, dpi=300, bbox_inches='tight')
            print(f"月度总出力图已保存到: {monthly_plot_filename}")
        
        # 绘制8月份随机11天出力曲线图
        august_fig = plot_random_august_period(data, start_date_obj, energy_type, location)
        
        # 保存8月份随机出力曲线图
        if august_fig:
            august_filename = f"{start_date_obj.year}_{energy_type}_{location}_august_random.png"
            august_fig.savefig(august_filename, dpi=300, bbox_inches='tight')
            print(f"8月份随机出力曲线图已保存到: {august_filename}")
        
        # 分析高出力期间
        high_power_periods = analyze_high_power_periods(data, start_idx, end_idx, energy_type, high_power_threshold)
        
        # 绘制高出力场景图
        high_power_fig = plot_high_power_scenarios(data, start_idx, end_idx, high_power_periods, 
                                                 start_date, min_duration, energy_type, high_power_threshold)
        
        # 保存高出力场景图
        if high_power_fig:
            high_power_filename = f"{start_date_obj.year}_{energy_type}_{location}_high_power_scenarios.png"
            high_power_fig.savefig(high_power_filename, dpi=300, bbox_inches='tight')
            print(f"高出力场景图已保存到: {high_power_filename}")
        
        # 准备输出数据
        output_data = []
        
        for period in low_power_periods:
            start_day = period[0]
            end_day = period[-1]
            duration = len(period)
            period_start = start_date_obj + pd.Timedelta(days=start_day)
            period_end = start_date_obj + pd.Timedelta(days=end_day)
            
            # 计算加权平均值
            weighted_avg = calculate_weighted_average(data, start_idx, period, energy_type)
            
            output_data.append({
                '开始日期': period_start.strftime('%Y-%m-%d'),
                '结束日期': period_end.strftime('%Y-%m-%d'),
                '持续时间(天)': duration,
                '加权平均值': f'{weighted_avg:.3f}'
            })
        
        # 创建输出DataFrame并保存到Excel
        if output_data:
            output_df = pd.DataFrame(output_data)
            output_filename = f"{start_date_obj.year}_{energy_type}_{location}.xlsx"
            output_df.to_excel(output_filename, index=False)
            print(f"分析结果已保存到: {output_filename}")
        
        # 准备高出力数据输出（只输出符合最小持续时间要求的场景）
        high_power_output = []
        
        filtered_high_power_periods = [period for period in high_power_periods if len(period) >= min_duration]
        for period in filtered_high_power_periods:
            start_day = period[0]
            end_day = period[-1]
            duration = len(period)
            period_start = start_date_obj + pd.Timedelta(days=start_day)
            period_end = start_date_obj + pd.Timedelta(days=end_day)
            
            # 计算加权平均值
            weighted_avg = calculate_weighted_average(data, start_idx, period, energy_type)
            
            high_power_output.append({
                '开始日期': period_start.strftime('%Y-%m-%d'),
                '结束日期': period_end.strftime('%Y-%m-%d'),
                '持续时间(天)': duration,
                '加权平均值': f'{weighted_avg:.3f}'
            })
        
        # 创建高出力输出DataFrame并保存到Excel
        if high_power_output:
            high_power_df = pd.DataFrame(high_power_output)
            high_power_filename = f"{start_date_obj.year}_{energy_type}_{location}_high_power.xlsx"
            high_power_df.to_excel(high_power_filename, index=False)
            print(f"高出力分析结果已保存到: {high_power_filename}")
        else:
            print(f"未发现持续时间大于等于{min_duration}天且出力大于等于{high_power_threshold}的高出力期间")
            
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main()
