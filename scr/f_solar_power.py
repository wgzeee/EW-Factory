import numpy as np

def f_solar_power(G, A, eta, G_threshold=100):
    """
    计算光伏发电功率
    
    参数:
        G (float or ndarray): 光照强度 (W/m²)，可以是标量、向量或矩阵
        A (float): 光伏组件的有效面积 (m²)
        eta (float): 光伏组件的转换效率 (0 < eta < 1)
        G_threshold (float, optional): 光照强度阈值 (W/m²)，大于该值开始并网输出。默认值为100
        
    返回:
        ndarray: 光伏发电功率 (W)，与 G 的维度相同
    
    异常:
        ValueError: 当输入参数不满足要求时抛出
    """
    # 检查输入参数
    if A <= 0:
        raise ValueError('光伏组件面积 A 必须大于 0')
    
    if eta <= 0 or eta >= 1:
        raise ValueError('转换效率 eta 必须在 0 到 1 之间')
    
    # 将输入转换为numpy数组以支持数组运算
    G = np.array(G)
    
    # 初始化功率输出为0
    power = np.zeros_like(G)
    
    # 计算光伏发电功率（仅当 G >= G_threshold 时）
    mask = G >= G_threshold
    power[mask] = G[mask] * A * eta
    
    return power