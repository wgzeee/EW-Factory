import cdsapi
from IPython.display import clear_output

def download(var, year, month=None, day=None, time=None, area=None, dataset="reanalysis-era5-single-levels"):
    '''
    下载气象数据，默认下载era5全球模型"reanalysis-era5-single-levels",建议外部循环逐年下载以防中断。
    参数：
        var_list: list, 变量名称列表，例如 ['surface_solar_radiation_downwards']
        year_list: list, 年份列表，例如 [2001, 2002]
        month, day, time: 可选时间范围，默认下载全年、全月、全天
        area: 下载方形区域，格式为 [左下经度, 左下纬度, 右上经度, 右上纬度]
        dataset: CDS数据集名称，默认单层再分析
    '''
    client = cdsapi.Client()

    if area is None:
        area = []
    if month is None:
        month = [f"{i:02d}" for i in range(1, 13)]
    if day is None:
        day = [f"{i:02d}" for i in range(1, 32)]
    if time is None:
        time = [f"{i:02d}:00" for i in range(24)]
    if area is None:
        area = [53.75, 73.5, 3.75, 135.25]
    req = {
        "product_type": "reanalysis",
        "variable": [var],
        "year": [year],
        "month": month,
        "day": day,
        "time": time,
        "format": "netcdf",
        "area": area,
    }
    print(f"正在下载: {var} 年份: {year}")
    client.retrieve(dataset, req).download(f"download/{var}/{var}_{year}.nc")
    clear_output()