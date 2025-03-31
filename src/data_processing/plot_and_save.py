import matplotlib.pyplot as plt

def plot_and_save_solar_power(solar_power, lon_grid, lat_grid, output_dir="output"):
    """
    绘制并保存太阳辐照强度分布图
    
    Args:
        solar_power: 3D数组 (time, lat, lon)
        lon_grid: 经度网格
        lat_grid: 纬度网格
        output_dir: 输出目录
    """
    import os
    import imageio
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 存储所有图片文件名
    image_files = []
    
    # 遍历每个时间点
    for t in range(solar_power.shape[0]):
        plt.figure(figsize=(10, 8))
        plt.rcParams['font.sans-serif']=['Microsoft YaHei']
        
        # 绘制网格图
        pcm = plt.pcolormesh(lon_grid, lat_grid, solar_power[t], 
                            cmap='viridis', shading='auto',
                            edgecolors='white', linewidth=0.5)
        plt.colorbar(pcm)
        plt.title(f'太阳辐照强度分布 (时间点: {t+1})')
        plt.xlabel('经度')
        plt.ylabel('纬度')
        
        # 保存为jpg
        jpg_path = os.path.join(output_dir, f'solar_power_{t:03d}.jpg')
        plt.savefig(jpg_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        image_files.append(jpg_path)
    
    # 生成GIF动画
    images = []
    for filename in image_files:
        images.append(imageio.imread(filename))
    
    gif_path = os.path.join(output_dir, 'solar_power_animation.gif')
    imageio.mimsave(gif_path, images, duration=0.5)  # 每帧停留0.5秒
    
    print(f"已保存{len(image_files)}张图片到 {output_dir}")
    print(f"已生成动画文件: {gif_path}")

if __name__ == "__main__":
    # ... existing code ...
    
    G = ssrd_province / 3600
    solar_power = f_solar_power.f_solar_power(G)
    
    # 调用新函数替代原来的绘图代码
    plot_and_save_solar_power(solar_power, lon_grid, lat_grid, 
                             output_dir="d:\\wgzee\\Documents\\GitHub\\EW-Factory\\output")
    
    # ... rest of the code ...