import matplotlib.pyplot as plt
import os
import imageio
import numpy as np

def save_png(power, lon_grid, lat_grid, output_dir="output", bar_type='self_calculate', minmax=[0,0.6]):

    """
    绘制并保存太阳辐照强度分布图
    
    Args:
        power: 3D数组风电/光伏 (time, lat, lon)
        lon_grid: 经度网格
        lat_grid: 纬度网格
        output_dir: 输出目录
    """
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 存储所有图片文件名
    image_files = []
    
    # 遍历每个时间点
    for t in range(power.shape[0]):
        plt.figure(figsize=(10, 8))
        plt.rcParams['font.sans-serif']=['Microsoft YaHei']
        
        # 绘制网格图
        pcm = plt.pcolormesh(lon_grid, lat_grid, power[t], 
                            cmap='viridis', shading='auto',
                            edgecolors='white', linewidth=0.5)
        plt.colorbar(pcm)  # 添加颜色条
        if bar_type == 'self_calculate':
            pcm.set_clim(vmin=np.nanmin(power[t]), vmax=np.nanmax(power[t]))
        else:
            pcm.set_clim(vmin=minmax[0], vmax=minmax[1])
        
        plt.xlabel('经度')
        plt.ylabel('纬度')
        
        # 设置固定的坐标轴范围
        plt.xlim([np.min(lon_grid), np.max(lon_grid)])
        plt.ylim([np.min(lat_grid), np.max(lat_grid)])
        
        # 保存图像时使用固定的尺寸
        save_path = os.path.join(output_dir, f"太阳能电量 {t}.png")
        plt.title(f'太阳能逐小时容量系数 ({t} UTC)')
        plt.savefig(save_path, dpi=100, bbox_inches=None)  # 不使用bbox_inches='tight'，保持固定尺寸
        
        plt.show()
        plt.close()
        image_files.append(save_path)
    return image_files
    
def generate_gif(image_files, output_dir, dur=0.25):
    """
    生成GIF动画
    
    Args:
        image_files: 图像文件路径列表
        output_dir: 输出目录
        duration: 每帧停留时间（秒）
    """
    
    # 存储所有图片
    images = []
    for filename in image_files:
        images.append(imageio.imread(filename))
    
    gif_path = os.path.join(output_dir, 'solar_power_animation.gif')
    # 设置loop=0使GIF无限循环播放
    imageio.mimsave(gif_path, images, duration=dur, loop=0)
    
    print(f"已保存{len(image_files)}张图片到 {output_dir}")
    print(f"已生成动画文件: {gif_path}")
    
    return gif_path

# 调用生成GIF函数



    
