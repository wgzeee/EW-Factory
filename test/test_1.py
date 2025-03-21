import sys

# 将项目的src文件夹路径添加到sys.path中
# 这样可以在当前脚本中直接导入src文件夹中的模块
sys.path.append("../src")

import extract_province_var

if __name__ == "__main__":
    file_path = r'E:\\电力气象\\太阳辐射\\ERA5_land_hourily_ssrd_202401.nc'
    shapefile_path = r'E:\\电力气象\\地图\\ChinaAdminDivisonSHP-master\\2. Province\\province.shp'
    
    province_name = '山东省'
    var_name = 'ssrd'
    
    ssrd_province, lon_grid, lat_grid = extract_province_var(file_path, shapefile_path, province_name, var_name)
    print(f"提取的{province_name}{var_name}数据形状: {ssrd_province.shape}")