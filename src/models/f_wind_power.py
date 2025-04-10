import numpy as np

def f_wind_power(v, rated_power=1000, cut_in=3.0, rated=12.0, cut_out=25.0, 
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

