import numpy as np

def f_wind_power(v, rated_power=1, cut_in=3.0, rated=12.0, cut_out=25.0, 
                 height_correction=False, ref_height=10, hub_height=80, alpha=0.143):
    """
    计算风力发电功率
    
    参数:
        v (float or ndarray): 风速 (m/s)，可以是标量、向量或矩阵
        rated_power (float): 风机额定功率 (kW)
        cut_in (float): 切入风速 (m/s)，风机开始发电的最小风速
        rated (float): 额定风速 (m/s)，风机达到额定功率的风速
        cut_out (float): 切出风速 (m/s)，风机停止发电的风速
        height_correction (bool): 是否进行高度修正，默认为False
        ref_height (float): 参考高度 (m)，通常为气象数据的测量高度
        hub_height (float): 风机轮毂高度 (m)
        alpha (float): 风切变指数，用于高度修正计算
        
    返回:
        ndarray: 风力发电功率 (kW)，与 v 的维度相同
    
    异常:
        ValueError: 当输入参数不满足要求时抛出
    """
    # 检查输入参数
    if rated_power <= 0:
        raise ValueError('额定功率必须大于0')
    
    if cut_in >= rated or rated >= cut_out:
        raise ValueError('切入风速必须小于额定风速，额定风速必须小于切出风速')
    
    # 将输入转换为numpy数组以支持向量化运算
    v = np.array(v)
    
    # 如果需要高度修正，将参考高度的风速修正到轮毂高度
    if height_correction and ref_height != hub_height:
        v = v * (hub_height / ref_height) ** alpha
    
    # 初始化功率输出为0
    power = np.zeros_like(v)
    
    # 处理NaN值
    nan_mask = np.isnan(v)
    power[nan_mask] = np.nan
    
    # 计算风力发电功率
    # 1. 风速低于切入风速或高于切出风速时，功率为0
    # 2. 风速在切入风速和额定风速之间时，功率按照风速的立方增长
    # 3. 风速在额定风速和切出风速之间时，功率为额定功率
    
    # 风速在切入风速和额定风速之间
    mask1 = (v >= cut_in) & (v < rated) & (~nan_mask)
    power[mask1] = rated_power * ((v[mask1] - cut_in) / (rated - cut_in)) ** 3
    
    # 风速在额定风速和切出风速之间
    mask2 = (v >= rated) & (v <= cut_out) & (~nan_mask)
    power[mask2] = rated_power
    
    return power


def calculate_wind_speed(u, v):
    """
    根据ERA5的U和V方向风速分量计算合成风速
    
    参数:
        u (float or ndarray): U方向风速分量 (m/s)，可以是标量、向量或矩阵
        v (float or ndarray): V方向风速分量 (m/s)，可以是标量、向量或矩阵
        
    返回:
        ndarray: 合成风速 (m/s)，与输入维度相同
    """
    # 将输入转换为numpy数组以支持向量化运算
    u = np.array(u)
    v = np.array(v)
    
    # 检查u和v的维度是否一致
    if u.shape != v.shape:
        raise ValueError('U和V方向风速分量的维度必须一致')
    
    # 计算合成风速（勾股定理）
    wind_speed = np.sqrt(u**2 + v**2)
    
    return wind_speed


def calculate_wind_direction(u, v):
    """
    根据ERA5的U和V方向风速分量计算风向（气象学角度）
    
    参数:
        u (float or ndarray): U方向风速分量 (m/s)，可以是标量、向量或矩阵
        v (float or ndarray): V方向风速分量 (m/s)，可以是标量、向量或矩阵
        
    返回:
        ndarray: 风向角度 (度)，范围为[0, 360)，表示风的来向
                 0/360表示北风（从北方吹来），90表示东风，180表示南风，270表示西风
    """
    # 将输入转换为numpy数组以支持向量化运算
    u = np.array(u)
    v = np.array(v)
    
    # 检查u和v的维度是否一致
    if u.shape != v.shape:
        raise ValueError('U和V方向风速分量的维度必须一致')
    
    # 计算风向（弧度）- 注意这里计算的是风吹向的方向
    wind_dir_rad = np.arctan2(v, u)
    
    # 转换为气象学角度（风的来向）- 先转为度，然后调整
    wind_dir_deg = np.degrees(wind_dir_rad)
    
    # 调整为气象学角度：先转为风的来向（反向），然后调整到[0,360)范围
    wind_dir_met = (270 - wind_dir_deg) % 360
    
    return wind_dir_met


def calculate_wind_power_from_uv(u, v, rated_power=1, cut_in=3.0, rated=12.0, cut_out=25.0,
                                height_correction=False, ref_height=10, hub_height=80, alpha=0.143):
    """
    根据ERA5的U和V方向风速分量直接计算风力发电功率
    
    参数:
        u (float or ndarray): U方向风速分量 (m/s)，可以是标量、向量或矩阵
        v (float or ndarray): V方向风速分量 (m/s)，可以是标量、向量或矩阵
        rated_power (float): 风机额定功率 
        cut_in (float): 切入风速 (m/s)，风机开始发电的最小风速
        rated (float): 额定风速 (m/s)，风机达到额定功率的风速
        cut_out (float): 切出风速 (m/s)，风机停止发电的风速
        height_correction (bool): 是否进行高度修正，默认为False
        ref_height (float): 参考高度 (m)，通常为气象数据的测量高度
        hub_height (float): 风机轮毂高度 (m)
        alpha (float): 风切变指数，用于高度修正计算
        
    返回:
        ndarray: 风力发电功率 ，与输入维度相同
    """
    # 计算合成风速
    wind_speed = calculate_wind_speed(u, v)
    
    # 使用f_wind_power函数计算风力发电功率
    power = f_wind_power(wind_speed, rated_power, cut_in, rated, cut_out, 
                         height_correction, ref_height, hub_height, alpha)
    
    return power




