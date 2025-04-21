import matplotlib.pyplot as plt
import os
import imageio
import numpy as np
import seaborn as sns

def plot_monthly_boxplot(monthly_energys, province_name):
    """
    根据monthly_energys数据绘制每个月的箱型图
    
    Args:
        monthly_energys: 月度能量数据，形状为(月份数, lat, lon)
        province_name: 省份名称
        output_dir: 输出目录，如果为None则使用默认路径
    
    Returns:
        str: 保存的图像路径
    """
    # # 设置默认输出目录
    # if output_dir is None:
    #     output_dir = f"D:\\output\\solar_power\\{province_name}\\boxplot"
    
    # # 创建输出目录
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)
    
    # 准备数据：将每个月的2D数据转换为1D数组，用于箱型图
    monthly_data = []
    month_names = []
    
    for i in range(monthly_energys.shape[0]):
        # 提取非NaN值
        valid_data = monthly_energys[i].flatten()
        valid_data = valid_data[~np.isnan(valid_data)]
        monthly_data.append(valid_data)
        month_names.append(f"{i+1}月")
    
    # 创建图形
    plt.figure(figsize=(14, 8))
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 用来正常显示中文标签
    
    # 绘制箱型图
    boxplot = plt.boxplot(monthly_data, patch_artist=True, labels=month_names)
    
    # 设置箱型图颜色
    colors = plt.cm.viridis(np.linspace(0, 1, len(monthly_data)))
    for patch, color in zip(boxplot['boxes'], colors):
        patch.set_facecolor(color)
    
    # 添加标题和标签
    plt.title(f'{province_name}各月太阳能电量分布', fontsize=16)
    plt.xlabel('月份', fontsize=16)
    plt.ylabel('电量 (按小时归一化)', fontsize=16)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 添加均值点和数值标注
    for i, data in enumerate(monthly_data):
        mean_val = np.mean(data)
        plt.plot(i+1, mean_val, 'ro', ms=8)  # 红色点表示均值
        plt.text(i+1, mean_val, f'{mean_val:.2f}', 
                 ha='center', va='bottom', fontsize=14)
    
    # 调整布局
    plt.tight_layout()
    plt.show()
    
    # 保存图像
    # save_path = os.path.join(output_dir, f"{province_name}_月度太阳能电量箱型图.png")
    # plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    # print(f"已保存月度箱型图到: {save_path}")
    # return save_path

def plot_monthly_comparison(monthly_energys, province_name, output_dir=None):
    """
    绘制月度能量数据的均值、中位数和标准差比较图
    
    Args:
        monthly_energys: 月度能量数据，形状为(月份数, lat, lon)
        province_name: 省份名称
        output_dir: 输出目录，如果为None则使用默认路径
    
    Returns:
        str: 保存的图像路径
    """
    # # 设置默认输出目录
    # if output_dir is None:
    #     output_dir = f"D:\\output\\solar_power\\{province_name}\\statistics"
    
    # # 创建输出目录
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)
    
    # 计算每个月的统计量
    months = range(1, monthly_energys.shape[0] + 1)
    means = []
    medians = []
    stds = []
    
    for i in range(monthly_energys.shape[0]):
        valid_data = monthly_energys[i].flatten()
        valid_data = valid_data[~np.isnan(valid_data)]
        means.append(np.mean(valid_data))
        medians.append(np.median(valid_data))
        stds.append(np.std(valid_data))
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(14, 8))
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    
    # 绘制均值和中位数的折线图
    ax.plot(months, means, 'o-', color='blue', linewidth=2, label='均值')
    ax.plot(months, medians, 's-', color='green', linewidth=2, label='中位数')
    
    # 添加标准差区域
    ax.fill_between(months, 
                    [m - s for m, s in zip(means, stds)], 
                    [m + s for m, s in zip(means, stds)], 
                    color='blue', alpha=0.2, label='标准差范围')
    
    # 设置x轴刻度
    ax.set_xticks(months)
    ax.set_xticklabels([f"{m}月" for m in months])
    
    # 添加标题和标签
    ax.set_title(f'{province_name}各月太阳能电量统计', fontsize=16)
    ax.set_xlabel('月份', fontsize=14)
    ax.set_ylabel('电量 (按小时归一化)', fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(fontsize=12)
    
    # 在每个数据点上标注数值
    for i, (mean, median) in enumerate(zip(means, medians)):
        ax.annotate(f'{mean:.2f}', (months[i], mean), 
                   textcoords="offset points", xytext=(0,10), ha='center')
        ax.annotate(f'{median:.2f}', (months[i], median), 
                   textcoords="offset points", xytext=(0,-15), ha='center')
    
    # 调整布局
    plt.tight_layout()
    plt.show()
    
    # 保存图像
    # save_path = os.path.join(output_dir, f"{province_name}_月度太阳能电量统计比较.png")
    # plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    # print(f"已保存月度统计比较图到: {save_path}")
    # return save_path

def plot_monthly_violin(monthly_energys, province_name):
    """
    根据monthly_energys数据绘制每个月的小提琴图
    
    Args:
        monthly_energys: 月度能量数据，形状为(月份数, lat, lon)
        province_name: 省份名称
    """
    # 准备数据：将每个月的2D数据转换为适合小提琴图的格式
    all_data = []
    all_months = []
    
    for i in range(monthly_energys.shape[0]):
        # 提取非NaN值
        valid_data = monthly_energys[i].flatten()
        valid_data = valid_data[~np.isnan(valid_data)]
        
        # 为每个数据点添加月份标签
        all_data.extend(valid_data)
        all_months.extend([f"{i+1}月"] * len(valid_data))
    
    # 创建图形
    plt.figure(figsize=(14, 8))
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 用来正常显示中文标签
    
    # 使用seaborn绘制小提琴图
    ax = sns.violinplot(x=all_months, y=all_data, palette="viridis", 
                        inner="quartile", cut=0, linewidth=1)
    
    # 添加均值点和数值标注
    means = []
    for i in range(monthly_energys.shape[0]):
        valid_data = monthly_energys[i].flatten()
        valid_data = valid_data[~np.isnan(valid_data)]
        mean_val = np.mean(valid_data)
        means.append(mean_val)
        
        # 在小提琴图上标注均值
        plt.plot(i, mean_val, 'ro', ms=8)  # 红色点表示均值
        plt.text(i, mean_val, f'{mean_val:.2f}', 
                 ha='center', va='bottom', fontsize=12)
    
    # 添加标题和标签
    plt.title(f'{province_name}各月太阳能电量分布', fontsize=18)
    plt.xlabel('月份', fontsize=16)
    plt.ylabel('电量 (按小时归一化)', fontsize=16)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 添加均值连线
    plt.plot(range(len(means)), means, 'b--', alpha=0.7, linewidth=2)
    
    # 调整y轴范围，确保标注可见
    y_min, y_max = plt.ylim()
    plt.ylim(y_min, y_max * 1.05)
    
    # 调整布局
    plt.tight_layout()
    plt.show()
    plt.close()


def plot_calendar_heatmap(daily_energys, time_array, region_name, cmap='viridis'):
    """
    根据每日数据绘制日历热力图，星期几作为列名，日期从上到下增加
    
    Args:
        daily_energys: 日能量数据，形状为(天数, lat, lon)
        time_array: 时间数组，包含每小时的日期信息
        region_name: 区域名称
        cmap: 颜色映射名称
    """
    # 提取日期信息 - 处理cftime对象
    import datetime as dt
    import calendar
    import pandas as pd
    from matplotlib.colors import Normalize, LinearSegmentedColormap
    import matplotlib.patches as patches
    
    # 从time_array中提取不重复的日期
    dates = []
    for t in time_array:
        # 创建日期字符串作为唯一标识符
        date = dt.datetime(t.year, t.month, t.day)
        # 如果这一天还没有添加过，则添加到列表中
        if date not in dates:
            dates.append(date)
    
    # 确保日期数量与daily_energys的第一维度匹配，给出错误
    if len(dates) != daily_energys.shape[0]:
        print(f"警告：日期数量({len(dates)})与数据维度({daily_energys.shape[0]})不匹配")
        raise ValueError("日期数量与数据维度不匹配，请检查数据")
    
    # 计算每天的平均能量值（去除NaN值）
    daily_means = np.nanmean(daily_energys, axis=(1, 2))

    # 创建包含日期和值的DataFrame
    df = pd.DataFrame({
        'date': dates,
        'value': daily_means
    })
    
    # 提取年、月、日、星期几
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day
    df['weekday'] = df['date'].dt.weekday  # 0是周一
    
    # 获取年份
    year = df['year'].iloc[0]
    
    # 创建一个包含所有月份的图形
    fig, axes = plt.subplots(4, 3, figsize=(16, 12))
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    
    # 设置全局标题
    fig.suptitle(f'{region_name} {year}年每日太阳能电量分布', fontsize=20)
    
    # 设置颜色范围
    vmin = df['value'].min()
    vmax = df['value'].max()
    
    # 创建自定义颜色映射，从深蓝到黄色
    if cmap == 'custom':
        colors = ['#2a0a4c', '#365c8d', '#2e9eb8', '#47c2a2', '#a0da6e', '#fde725']
        cmap = LinearSegmentedColormap.from_list('custom_cmap', colors, N=256)
    
    norm = Normalize(vmin=vmin, vmax=vmax)
    
    # 月份名称
    month_names = ['一月', '二月', '三月', '四月', '五月', '六月', 
                   '七月', '八月', '九月', '十月', '十一月', '十二月']
    
    # 星期名称 - 作为列名
    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    
    # 遍历每个月份
    for month_idx, month_name in enumerate(month_names):
        # 计算在子图网格中的位置
        row = month_idx // 3
        col = month_idx % 3
        
        ax = axes[row, col]
        
        # 设置子图标题
        ax.set_title(f'{month_name}-{year}', fontsize=14)
        
        # 获取当月的数据
        month_data = df[df['month'] == month_idx + 1]
        
        # 获取当月第一天星期几、当月的天数
        first_weekday, days_in_month = calendar.monthrange(year, month_idx + 1) # 0是周一
        
        # 计算当月有多少周
        weeks_in_month = (days_in_month + first_weekday - 1) // 7 + 1
        
        # 创建日历网格 - 日期从上到下增加
        day_num = 1
        
        # 绘制星期几标签（放在顶部）
        for i, weekday in enumerate(weekday_names):
            ax.text(i + 0.5, 0.2, weekday, ha='center', va='center', fontsize=10)
        
        # 绘制日历方块
        for week in range(weeks_in_month):
            for weekday in range(7):
                # 第一周需要考虑第一天的星期几
                if week == 0 and weekday < first_weekday:
                    # 这是上个月的日期，不显示
                    continue
                
                if day_num <= days_in_month:
                    # 查找对应的数据
                    day_data = month_data[month_data['day'] == day_num]
                    
                    if not day_data.empty:
                        value = day_data['value'].iloc[0]
                        color = plt.cm.get_cmap(cmap)(norm(value))
                    else:
                        # 如果没有数据，使用灰色
                        color = 'lightgray'
                    
                    # 绘制方块
                    rect = patches.Rectangle((weekday, -week-1), 0.9, 0.9, 
                                           facecolor=color, edgecolor='white', linewidth=1)
                    ax.add_patch(rect)
                    
                    # 添加日期数字和数值
                    if not day_data.empty:
                        ax.text(weekday + 0.45, -week - 1 + 0.65, f"{day_num}", 
                               ha='center', va='center', fontsize=9, color='white')
                        ax.text(weekday + 0.45, -week - 1 + 0.35, f"{value:.2f}", 
                               ha='center', va='center', fontsize=8, color='white')
                    
                    day_num += 1
        
        # 设置坐标轴范围和隐藏刻度
        ax.set_xlim(-0.1, 7)
        ax.set_ylim(-weeks_in_month-0.1, 0.5)
        ax.set_xticks([])
        ax.set_yticks([])
        
        # 添加网格线
        for i in range(weeks_in_month + 1):
            ax.axhline(-i - 0.05, color='gray', linewidth=0.5, alpha=0.3)
        for j in range(8):
            ax.axvline(j - 0.05, color='gray', linewidth=0.5, alpha=0.3)
    
    # 添加颜色条
    cbar_ax = fig.add_axes([0.15, 0.05, 0.7, 0.02])
    sm = plt.cm.ScalarMappable(cmap=plt.cm.get_cmap(cmap), norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, cax=cbar_ax, orientation='horizontal')
    cbar.set_label('日均电量 (按小时归一化)', fontsize=12)
    
    # 调整布局
    plt.tight_layout(rect=[0, 0.08, 1, 0.95])
    plt.show()
    plt.close()
    
    return fig