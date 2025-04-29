import numpy as np

def f_solar_power(G, A=1, eta=0.2, G_threshold=100):
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
    
    # 将光照强度从J/m-2转换为w/m-2，并转换为numpy数组以支持向量化运算
    G = np.array(G / 3600)
    
    # 初始化功率输出为0
    power = np.zeros_like(G)
    
    # 计算光伏发电功率（仅当 G >= G_threshold 时）
    mask = G >= G_threshold
    power[mask] = G[mask] * A * eta
    power[np.isnan(G)] = np.nan
    
    return power


def f_solar_power_2(G, Pn=1, rn=1000):
    """
    根据分段函数计算光伏发电功率
    
    参数:
        G (float or ndarray): 光照强度 (W/m²)，可以是标量、向量或矩阵
        Pn (float): 额定功率 (W)，默认为1W（表示单位1）
        rn (float): 额定辐照强度 (W/m²)，默认为1000W/m²
        
    返回:
        ndarray: 光伏发电功率 (W)，与 G 的维度相同
    
    公式:
        P_e = {
            P_r * r/r_r, r ∈ [0, r_r)
            P_r,       r ∈ [r_r, ∞)
        }
    """
    # 将光照强度从J/m-2转换为w/m-2，并转换为numpy数组以支持向量化运算
    G = np.array(G / 3600)
    
    # 初始化功率输出数组
    power = np.zeros_like(G, dtype=float)
    
    # 处理NaN值
    power[np.isnan(G)] = np.nan
    
    # 应用分段函数
    # 第一段：0 <= G < r_r
    mask_low = (G >= 0) & (G < rn)
    power[mask_low] = Pn * (G[mask_low] / rn)
    
    # 第二段：G >= r_r
    mask_high = G >= rn
    power[mask_high] = Pn
    
    return power


def f_solar_power_with_temp(G, T, Pn=1, R_stc=1000, T_stc=25, k=-0.005):
    """
    计算考虑温度修正的光伏发电功率
    
    参数:
        G (float or ndarray): 光照强度 (W/m²)，可以是标量、向量或矩阵
        T (float or ndarray): 环境温度 (°C)，可以是标量、向量或矩阵
        Pn (float): 额定功率 (W)，默认为1W（表示单位1）
        R_stc (float): 标准测试条件下的辐照强度 (W/m²)，默认为1000W/m²
        T_stc (float): 标准测试条件下的温度 (°C)，默认为25°C
        k (float): 温度系数 (/°C)，默认为-0.004/°C
        
    返回:
        ndarray: 光伏发电功率 (W)，与 G 和 T 的维度相同
    
    公式:
        P = Pn * (G/R_stc) * [1 + k(T_c - T_stc)]
        T_c = T + 30*G/R_stc
        
    其中:
        P: 光伏发电功率
        Pn: 额定功率
        G: 实际辐照强度
        R_stc: 标准测试条件下的辐照强度
        k: 温度系数
        T_c: 电池温度
        T: 环境温度
        T_stc: 标准测试条件下的温度
    """
    # 检查G和T的维度是否一致
    if G.shape != T.shape:
        raise ValueError('光照强度G和温度T的维度必须一致')
    
    # 将光照强度从J/m-2转换为w/m-2，并转换为numpy数组以支持向量化运算
    G = np.array(G / 3600)
    # 将温度从K转换为°C
    T = np.array(T) - 273.15
    
    # 初始化功率输出数组
    power = np.zeros_like(G, dtype=float)
    
    # 处理NaN值
    nan_mask = np.isnan(G) | np.isnan(T)
    
    # 计算电池温度
    T_cell = T + 30 * G / R_stc
    
    # 计算温度修正系数
    temp_correction = 1 + k * (T_cell - T_stc)
    
    # 计算光伏发电功率
    power = Pn * (G / R_stc) * temp_correction
    
    # 负值修正（温度过高或辐照过低时可能出现）
    power[power < 0] = 0
    
    # 处理NaN值
    power[nan_mask] = np.nan
    
    return power