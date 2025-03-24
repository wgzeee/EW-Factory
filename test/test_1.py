import sys

# 添加项目根目录到系统路径
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

# 导入项目模块
from src.data_processing import data_loader
from src.models import wind_model, solar_model
from src.analysis import statistics, aggregation
from src.visualization import map_visualization, time_series_visualization
from src.utils import config_utils

if __name__ == "__main__":
    file_path = "E:\\电力气象\\era5\\2024\\ssrd\\ssrd_2024.nc"
    shapefile_path = "E:\\电力气象\\地图\\ChinaAdminDivisonSHP-master\\2. Province\\province.shp"
    
    province_name = '山东省'
    var_name = 'ssrd'
    
    ssrd_province, lon_grid, lat_grid = extract_province_var.extract_province_var(file_path, shapefile_path, province_name, var_name)
    print(f"提取的{province_name}{var_name}数据形状: {ssrd_province.shape}")