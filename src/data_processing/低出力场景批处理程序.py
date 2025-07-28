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
        if mean <= 0.1:
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
        
        # 计算加权平均值
        weighted_avg = calculate_weighted_average(data, start_idx, period, energy_type)
        
        # 绘制数据
        axes[idx].plot(time_series, scenario_data, 'b-', linewidth=1.5, label='出力值')
        axes[idx].axhline(y=weighted_avg, color='r', linestyle='--', label=f'加权平均值: {weighted_avg:.3f}')
        
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

def plot_monthly_power(data, start_date_obj, energy_type, location, color='#2ecc71'):
    """绘制月度总出力图"""
    # 创建新的图表
    fig, ax = plt.subplots(figsize=(20, 6))  # 增加宽度
    
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
    bars = ax.bar(month_names, monthly_power, color=color)  # 使用传入的颜色
    
    # 在柱子上添加数值标签
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom',
                fontsize=11)
    
    # 设置图表格式
    ax.set_title(f'{start_date_obj.year}年{location}{energy_type}', fontsize=20, pad=21)
    ax.set_xlabel('月', fontsize=18)  # 修改x轴标签
    ax.set_ylabel('', fontsize=18)
    
    # 设置刻度标签字体大小
    ax.tick_params(axis='both', labelsize=14)
    
    plt.tight_layout()
    return fig

def plot_daily_power(data, start_date_obj, energy_type, location, color='#2ecc71'):
    """绘制每日总出力图"""
    # 创建新的图表
    fig, ax = plt.subplots(figsize=(20, 6))  # 增加宽度
    
    # 计算每日的总出力
    daily_power = []
    day_labels = []
    selected_indices = []
    
    # 计算每月的天数
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if start_date_obj.year % 4 == 0 and (start_date_obj.year % 100 != 0 or start_date_obj.year % 400 == 0):
        days_in_month[1] = 29
    
    # 计算总天数
    total_days = sum(days_in_month)
    
    # 处理所有日期的数据
    for day in range(total_days):
        day_start = day * 24
        day_end = (day + 1) * 24
        
        # 提取当天数据并计算总和
        day_data = data[day_start:day_end]
        daily_power.append(np.sum(day_data))
        current_date = start_date_obj + pd.Timedelta(days=day)
        day_labels.append(f'{current_date.month}.{current_date.day}')
        
        # 只选择每周的第一天作为标签点
        if day % 7 == 0:  # 每周的第1天
            selected_indices.append(day)
    
    # 绘制柱状图
    bars = ax.bar(range(len(daily_power)), daily_power, color=color)  # 使用传入的颜色
    
    # 设置图表格式
    ax.set_title(f'{start_date_obj.year}年{location}{energy_type}', fontsize=20, pad=21)
    ax.set_xlabel('日期', fontsize=18)
    ax.set_ylabel('', fontsize=18)
    
    # 设置x轴标签，只显示每周第一天
    ax.set_xticks(selected_indices)
    ax.set_xticklabels([day_labels[i] for i in selected_indices], fontsize=12, rotation=45)
    
    # 设置y轴刻度标签字体大小
    ax.tick_params(axis='y', labelsize=14)
    
    plt.tight_layout()
    return fig

def plot_weekly_power(data, start_date_obj, energy_type, location, color='#2ecc71'):
    """绘制每周总出力图"""
    # 创建新的图表
    fig, ax = plt.subplots(figsize=(20, 6))
    
    # 计算每周的总出力
    weekly_power = []
    week_labels = []
    
    # 计算实际可用的周数（基于数据长度）
    total_hours = len(data)
    total_weeks = total_hours // (7 * 24)  # 每周7天 * 24小时
    
    if total_weeks == 0:
        print("警告：数据长度不足一周，无法生成周统计图")
        return None
    
    # 处理所有周的数据
    for week in range(total_weeks):
        week_start = week * 7 * 24
        week_end = min((week + 1) * 7 * 24, total_hours)  # 确保不超出数据范围
        
        # 提取当周数据并计算总和
        week_data = data[week_start:week_end]
        weekly_power.append(np.sum(week_data))
        
        # 使用周数作为标签
        week_labels.append(str(week + 1))
    
    # 如果没有有效数据，返回None
    if not weekly_power:
        print("警告：没有有效的周数据")
        return None
    
    # 绘制柱状图
    bars = ax.bar(week_labels, weekly_power, color=color)
    
    # 在柱子上添加数值标签
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom',
                fontsize=11)
    
    # 设置图表格式
    ax.set_title(f'{start_date_obj.year}年{location}{energy_type}', fontsize=20, pad=21)
    ax.set_xlabel('周', fontsize=18)
    ax.set_ylabel('', fontsize=18)
    
    # 根据能源类型设置y轴范围
    if energy_type == "风电":
        ax.set_ylim(0, max(weekly_power) * 1.1 if weekly_power else 100)  # 动态设置范围
    else:
        ax.set_ylim(0, max(weekly_power) * 1.1 if weekly_power else 50)   # 动态设置范围
    
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
    
    # 计算每天的平均值（考虑光伏特性）
    daily_avgs = []
    for day in range(11):  # 11天
        day_start = day * 24
        day_end = (day + 1) * 24
        daily_data = period_data[day_start:day_end]
        
        if energy_type == "光伏":
            # 对于光伏数据，只考虑大于等于0.001的值（白天数据）
            daytime_data = daily_data[daily_data >= 0.001]
            daily_avg = np.mean(daytime_data) if len(daytime_data) > 0 else 0
        else:
            # 对于风电数据，考虑所有数据
            daily_avg = np.mean(daily_data)
        daily_avgs.append(daily_avg)
    
    # 计算整个期间的平均值
    avg = np.mean(daily_avgs)
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(15, 6))
    
    # 绘制数据
    ax.plot(time_series, period_data, 'b-', linewidth=1.5, label='出力值')
    ax.axhline(y=avg, color='r', linestyle='--', 
               label=f'日均值平均: {avg:.3f}\n(已剔除夜间数据)' if energy_type == "光伏" else f'日均值平均: {avg:.3f}')
    
    # 设置图表格式
    ax.set_title(f'{start_date_obj.year}年{location}{energy_type}', 
                 fontsize=14, pad=15)
    ax.set_xlabel('时间', fontsize=12)
    ax.set_ylabel('', fontsize=12)
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

def analyze_low_power_probability(low_power_periods, start_date_obj):
    """分析长时低出力问题的月度概率分布"""
    # 初始化每月发生次数
    monthly_occurrences = {i: 0 for i in range(1, 13)}
    total_occurrences = 0
    
    for period in low_power_periods:
        # 计算每个时期的开始和结束日期
        start_day = period[0]
        end_day = period[-1]
        period_start = start_date_obj + pd.Timedelta(days=start_day)
        period_end = start_date_obj + pd.Timedelta(days=end_day)
        
        # 计算持续时间
        duration = len(period)
        
        # 如果跨月，计算每个月的时间占比
        if period_start.month != period_end.month:
            # 计算第一个月的天数
            first_month_days = pd.Period(f'{period_start.year}-{period_start.month}').days_in_month - period_start.day + 1
            # 计算第二个月的天数
            second_month_days = period_end.day
            
            # 根据占比决定统计到哪个月
            if first_month_days >= second_month_days:
                monthly_occurrences[period_start.month] += 1
            else:
                monthly_occurrences[period_end.month] += 1
        else:
            # 如果是在同一个月内，直接统计到该月
            monthly_occurrences[period_start.month] += 1
        
        total_occurrences += 1
    
    # 计算每月概率
    monthly_probabilities = {}
    for month, count in monthly_occurrences.items():
        if total_occurrences > 0:
            monthly_probabilities[month] = count / total_occurrences
        else:
            monthly_probabilities[month] = 0
    
    return monthly_probabilities, total_occurrences

def plot_monthly_probability(monthly_probabilities, total_occurrences, start_date_obj, energy_type, location, color='#3498db'):
    """绘制月度低出力概率分布图"""
    # 创建新的图表
    fig, ax = plt.subplots(figsize=(6, 6))  # 缩小宽度至原来的30%
    
    # 准备数据
    months = list(monthly_probabilities.keys())
    probabilities = list(monthly_probabilities.values())
    month_labels = [str(month) for month in months]  # 只显示阿拉伯数字
    
    # 绘制柱状图
    bars = ax.bar(month_labels, probabilities, color=color)  # 使用传入的颜色
    
    # 在柱子上添加数值标签，只显示整数百分比
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height*100)}%',  # 转换为整数百分比
                ha='center', va='bottom',
                fontsize=11)
    
    # 设置图表格式
    ax.set_title(f'{start_date_obj.year}年{location}{energy_type}', 
                 fontsize=20, pad=21)
    ax.set_xlabel('月', fontsize=18)
    ax.set_ylabel('', fontsize=18)
    
    # 设置y轴范围为0到1
    ax.set_ylim(0, 1)
    
    # 设置刻度标签字体大小
    ax.tick_params(axis='both', labelsize=14)
    
    plt.tight_layout()
    return fig

def main():
    try:
        # 获取当前文件夹路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 获取用户输入的日期范围
        start_date = input("请输入起始日期 (YYYY-MM-DD): ")
        end_date = input("请输入结束日期 (YYYY-MM-DD): ")
        
        # 获取最小持续时间参数
        while True:
            try:
                min_duration = int(input("请输入最小持续时间（天）: "))
                if min_duration > 0:
                    break
                print("请输入大于0的数字")
            except ValueError:
                print("请输入有效的数字")
        
        # 获取当前文件夹中的所有CSV文件
        csv_files = [f for f in os.listdir(current_dir) if f.endswith('.csv')]
        
        if not csv_files:
            print("错误：在当前文件夹中未找到CSV文件")
            return
            
        print(f"找到以下CSV文件：")
        for i, file in enumerate(csv_files, 1):
            print(f"{i}. {file}")
        
        # 让用户选择要处理的文件
        while True:
            try:
                file_choice = int(input(f"请输入要处理的文件编号 (1-{len(csv_files)}): "))
                if 1 <= file_choice <= len(csv_files):
                    selected_file = csv_files[file_choice - 1]
                    break
                else:
                    print(f"请输入1到{len(csv_files)}之间的数字")
            except ValueError:
                print("请输入有效的数字")
        
        # 手动输入图名关键字
        print("\n请输入图名关键字（例如：光伏、风电、太阳能等）：")
        chart_keyword = input("图名关键字: ").strip()
        
        # 验证输入
        if not chart_keyword:
            print("错误：图名关键字不能为空")
            return
        
        # 选择出图颜色
        print("\n请选择出图颜色：")
        print("1. 绿色 (#2ecc71)")
        print("2. 蓝色 (#3498db)")
        print("3. 红色 (#e74c3c)")
        print("4. 橙色 (#f39c12)")
        print("5. 紫色 (#9b59b6)")
        print("6. 青色 (#1abc9c)")
        print("7. 自定义颜色")
        
        while True:
            try:
                color_choice = int(input("请输入颜色选项 (1-7): "))
                if 1 <= color_choice <= 7:
                    break
                else:
                    print("请输入1到7之间的数字")
            except ValueError:
                print("请输入有效的数字")
        
        # 根据选择设置颜色
        if color_choice == 1:
            chart_color = '#2ecc71'  # 绿色
        elif color_choice == 2:
            chart_color = '#3498db'  # 蓝色
        elif color_choice == 3:
            chart_color = '#e74c3c'  # 红色
        elif color_choice == 4:
            chart_color = '#f39c12'  # 橙色
        elif color_choice == 5:
            chart_color = '#9b59b6'  # 紫色
        elif color_choice == 6:
            chart_color = '#1abc9c'  # 青色
        else:
            chart_color = input("请输入自定义颜色代码 (例如 #ff0000): ")
        
        print(f"\n正在处理文件: {selected_file}")
        file_path = os.path.join(current_dir, selected_file)
        
        # 创建start_date_obj
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        
        # 读取CSV文件
        df = pd.read_csv(file_path)
        data = df.iloc[:, 0].values  # 假设第一列为出力数据
        
        # 计算数据索引
        start_idx = calculate_data_index(start_date)
        end_idx = calculate_data_index(end_date)
        
        # 获取地点（从文件名提取）
        location = get_energy_type_and_location(file_path)[1]
        
        # 使用手动输入的图名关键字
        energy_type = chart_keyword
        
        # 分析低出力期间
        low_power_periods = analyze_low_power_periods(data, start_idx, end_idx, energy_type)
        
        # 分析月度概率分布
        monthly_probabilities, total_occurrences = analyze_low_power_probability(low_power_periods, start_date_obj)
        
        # 绘制月度概率分布图
        probability_fig = plot_monthly_probability(monthly_probabilities, total_occurrences, 
                                                 start_date_obj, energy_type, location, chart_color)
        
        # 保存月度概率分布图
        if probability_fig:
            probability_filename = f"{start_date_obj.year}_{energy_type}_{location}_probability.png"
            probability_fig.savefig(probability_filename, dpi=300, bbox_inches='tight')
            print(f"月度概率分布图已保存到: {probability_filename}")
        
        # 绘制场景图
        fig = plot_low_power_scenarios(data, start_idx, end_idx, low_power_periods, 
                                     start_date, min_duration, energy_type)
        
        # 保存场景图
        if fig:
            plot_filename = f"{start_date_obj.year}_{energy_type}_{location}_scenarios.png"
            fig.savefig(plot_filename, dpi=300, bbox_inches='tight')
            print(f"场景图已保存到: {plot_filename}")
        
        # 绘制月度总出力图
        monthly_fig = plot_monthly_power(data, start_date_obj, energy_type, location, chart_color)
        
        # 保存月度总出力图
        if monthly_fig:
            monthly_plot_filename = f"{start_date_obj.year}_{energy_type}_{location}_monthly.png"
            monthly_fig.savefig(monthly_plot_filename, dpi=300, bbox_inches='tight')
            print(f"月度总出力图已保存到: {monthly_plot_filename}")
        
        # 绘制每日总出力图
        daily_fig = plot_daily_power(data, start_date_obj, energy_type, location, chart_color)
        
        # 保存每日总出力图
        if daily_fig:
            daily_plot_filename = f"{start_date_obj.year}_{energy_type}_{location}_daily.png"
            daily_fig.savefig(daily_plot_filename, dpi=300, bbox_inches='tight')
            print(f"每日总出力图已保存到: {daily_plot_filename}")
        
        # 绘制每周总出力图
        weekly_fig = plot_weekly_power(data, start_date_obj, energy_type, location, chart_color)
        
        # 保存每周总出力图
        if weekly_fig:
            weekly_plot_filename = f"{start_date_obj.year}_{energy_type}_{location}_weekly.png"
            weekly_fig.savefig(weekly_plot_filename, dpi=300, bbox_inches='tight')
            print(f"每周总出力图已保存到: {weekly_plot_filename}")
        
        # 绘制8月份随机11天出力曲线图
        august_fig = plot_random_august_period(data, start_date_obj, energy_type, location)
        
        # 保存8月份随机出力曲线图
        if august_fig:
            august_filename = f"{start_date_obj.year}_{energy_type}_{location}_august_random.png"
            august_fig.savefig(august_filename, dpi=300, bbox_inches='tight')
            print(f"8月份随机出力曲线图已保存到: {august_filename}")
        
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
            output_filename = f"{start_date_obj.year}_{energy_type}_{location}.xlsx"
            output_df = pd.DataFrame(output_data)
            output_df.to_excel(output_filename, index=False)
            print(f"分析结果已保存到: {output_filename}")
        else:
            print("未发现符合条件的低出力期间")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main()
