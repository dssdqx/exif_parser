import subprocess
import pandas as pd
import os

ExposureProgram_dict = {0: 'Not_Defined', 1: 'Manual', 2: 'Program_AE', 3: 'Aperture-priority_AE', 4: 'Shutter_speed_priority_AE',
                        5: 'Creative_(Slow speed)', 6: 'Action_(High speed)', 7: 'Portrait',
                        8: 'Landscape', 9: 'Bulb'}
MeteringMode_dict = {0: 'Unknown', 1: 'Average', 2: 'Center-weighted-average', 3: 'Spot', 4: 'Multi-spot',
                     5: 'Multi-segment', 6: 'Partial', 255: 'Other'}


def attention(tag: str, num: int):
    print('_________')
    print(f'\n{tag} has {num} values, use groups for better alignment and manually re-run step 1')
    print('_________')

def exif_parser(dir: str, home: str):
    find = f'exiftool -r -filename -GPSLongitude -GPSLatitude -GPSAltitude -Model -ImageSize -CreateDate -Aperture -ExposureTime -ExposureProgram -ISO -RtkFlag -ShutterType -MeteringMode -DewarpData -NTRIPHost -NTRIPMountPoint -DigitalZoomRatio -RtkStdLon -RtkStdLat -RtkStdHgt -DroneSerialNumber -T -n {dir} > {dir}out.txt'
    subprocess.run(find, shell=True, capture_output=True, text=True)

    w_tab = pd.read_csv((f'{dir}out.txt'), sep='\t', names=["photo", "lon", "lat", "height", "model", "image_size", "create_date", "Aperture", "Exposure", "program", "iso",
                                                            'flag', 'shutter', 'mode', 'dewarping', 'ntrip', 'mount_point', 'zoom_ratio', 'std_lon', 'std_lat', 'std_hgt', 'drone_SN'])
    df = pd.DataFrame(w_tab)
    df = df.query("Exposure != '-' ")
    df.reset_index(drop= True , inplace= True )

    df2 = df.copy()
    exposure_lst = []
    exposure = set()
    q = 0
    while q < len(df['Exposure']):
        value = df['Exposure'][q]
        a = float(1/float(value))
        b = int(round(a, 0))
        exposure.add(b)
        exposure_lst.append(b)
        df2.loc[q,'Exposure'] = int(b)
        if str(df.loc[q, 'dewarping']) == '-':
            df2.loc[q, 'dewarping'] = 'on'
  
        if str(df.loc[q, 'dewarping']) != '-':
            df2.loc[q, 'dewarping'] = 'off'

        if str(df.loc[q, 'ntrip']) == '-':
            df2.loc[q, 'ntrip'] = 'local_base'

        if str(df.loc[q, 'mount_point']) == '-':
            df2.loc[q, 'mount_point'] = 'none'

        if str(df.loc[q, 'ntrip']) != '-':
            df2.loc[q, 'ntrip'] = df['ntrip'][q] + ' - host connection'
        
        if str(df.loc[q, 'mount_point']) != '-':
            df2.loc[q, 'mount_point'] = df['mount_point'][q]

        q+=1
        
    df2.drop(['shutter','mode'], axis= 1 , inplace= True )
    df2 = df2.sort_values("create_date", ascending=True) 

    dewarping_mode = set()
    for i in df2['dewarping']:
        dewarping_mode.add(i)

    ntrip_mode = set()
    for i in df2['ntrip']:
        ntrip_mode.add(i)

    mount_point_mode = set()
    for i in df2['mount_point']:
        mount_point_mode.add(i)

    zoom_ratio_mode = set()
    for i in df2['zoom_ratio']:
        zoom_ratio_mode.add(i)

    drone_SN_set = set()
    for i in df2['drone_SN']:
        drone_SN_set.add(i)

    drone_SN_list = list(drone_SN_set)
    if len(drone_SN_list) > 1 and len(drone_SN_list) < 3:
        df2.loc[df2['drone_SN'] == drone_SN_list[0], 'drone_number'] = '1_drone'
        df2.loc[df2['drone_SN'] == drone_SN_list[1], 'drone_number'] = '2_drone'

    if len(drone_SN_set) == 1:
        df2.drop(['drone_SN'], axis= 1 , inplace= True )


    df2.to_excel(f'{home}\\out.xlsx', sheet_name='Sheet1', index = False)
    df_georef = df2.copy()

    flags_lst = []

    for (columnName, columnData) in df.items():
        #print('Column Name : ', columnName)
        #print('Column Contents : ', set(columnData.values))
        if columnName == 'Aperture':
            aperture = set(columnData.values)
        if columnName == 'model':
            model = set(columnData.values)
        if columnName == 'image_size':
            image_size = set(columnData.values)

        if columnName == 'create_date':
            date_capture = []
            for i in columnData.values:
                date_capture.append(i[0:10])

        if columnName == 'program':
            program = set(columnData.values)

        if columnName == 'iso':
            iso = set(columnData.values)

        if columnName == 'flag':
            flag = set(columnData.values)
            for i in columnData.values:
                flags_lst.append(i)

        if columnName == 'shutter':
            shutter = set(columnData.values)
        if columnName == 'mode':
            mode = set(columnData.values)
 
    for q in mode:
        for k, v in MeteringMode_dict.items():
            if int(q) == k:
                metering_name = str(v)

    for q in program:
        for k, v in ExposureProgram_dict.items():
            if int(q) == k:
                program_name = str(v)



    print(f'\ncamera model - {model}\nimage size - {image_size}\nflight date(yyyy-mm-dd) - {set(date_capture)}\nphotos - {len(df)}\n\naperture - {sorted(aperture)}\nshutter - {sorted(exposure)}\niso -{sorted(iso)}\nprogram - {program_name}\nrtk - {sorted(flag)}\nshutter - {shutter}\n'
          f'mode - {metering_name}\ndewarping - {dewarping_mode}\nzoom ratio mode - {zoom_ratio_mode}\nRTK correction from - {sorted(ntrip_mode)}\nMount point - {sorted(mount_point_mode)}\n')

    troubles = []
    for i in exposure:
        if i < 600:
            troubles.append(i)
    if len(troubles) > 3:
        print(f'\nshutter values are critical minimal {sorted(troubles)} possibility BLUR - NO FOCUS \nmaybe you should ask the pilot' 
            f' to use shutter speed priority mode with (1\\1000) value\n')


    for i in sorted(exposure):
        number = exposure_lst.count(i)
        pct = str(round(int(number)/int(len(df))*100,1))
        print(f'{i} value shutter - {number} photos, {pct}% ')

    print('\n_________________\n')

    for i in sorted(flag):
        number_flag = flags_lst.count(i)
        pct2 = str(round(int(number_flag)/int(len(flags_lst))*100,1))
        print(f'{i} value rtk flag - {number_flag} photos, {pct2}%')

    is_rtk_flag = df['flag'].eq('-').all()
    is_rtk_flag2 = df['flag'].eq('0').all()
    is_rtk_flag3 = df['flag'].eq('50').all()

    if is_rtk_flag == True:
        print('\nThis is not RTK flight, but it could be a PPK flight')
    if is_rtk_flag2 == True:
        print('\nThis is not a RTK flight')

    if is_rtk_flag3 != True or is_rtk_flag == True or is_rtk_flag2 == True  :
        df_georef2 = df_georef.query("flag == '50'")
        df_georef2.reset_index(drop= True , inplace= True )
        if len(df_georef2['flag']) != 0 and len(df_georef2['flag']) > 5 :
            df_georef.loc[df_georef['flag'] == '50', 'accuracy'] = 0.05
            df_georef.loc[df_georef['flag'] != '50', 'accuracy'] = 0.30
            print(f'\nprepared file {home}\\scan.photo.georef.txt\nwith field accuracy for each flag\n')
            df_georef.to_csv(f'{home}\\scan.photo.georef.txt', sep='\t', columns=["photo", "lon", "lat", "height", 'accuracy'], index=False) 

    print('_________________\n')


    def analyze_column(df, column_name):
        df = df.copy()
        df[column_name] = pd.to_numeric(df[column_name], errors='coerce')
        column = df[column_name]
        print(f'{column_name} max: {round(column.max(),4)}, min: {round(column.min(),4)}, mean: {round(column.mean(),4)}')

    is_rtk = df['std_lon'].ne('-').all()
    if is_rtk == True:
        analyze_column(df, 'std_lon')
        analyze_column(df, 'std_lat')
        analyze_column(df, 'std_hgt')

    if len(zoom_ratio_mode) > 1:
        attention('zoom ratio mode', len(zoom_ratio_mode))   # если включился зум - плохо, значений будет больше чем два нет смысла проверять на == 2 и т.д.

    if len(dewarping_mode) > 1:
        attention('DEWARPING ON/OFF', len(dewarping_mode))

    if len(drone_SN_set) > 1:
        print(f'\nAttention, for capture {len(drone_SN_set)} drones were used, so there may be problems. \nCheck metashape project and maybe need use chunks for processing\n')

    print(f'\nxlsx here {home}\\out.xlsx\n')

    os.remove(f'{dir}out.txt')


print('Based on ExifTool ver 12.60 (https://exiftool.org)')
print("""
  _____
 /     \\
|  O O  |
|   ^   |
|  \\_/  |
 \\_____/
""")


while True:
    u_input = input(r'folder ("c:\traceairroot\account\project\YYYY-MM-DD"): ')
    photos_folder = os.path.join(os.path.normpath(u_input), 'input', 'scan\\')
    origin_folder = os.path.normpath(u_input)
    try:
        exif_parser(photos_folder, origin_folder)
        print('\nnext folder...\n')
    except FileNotFoundError:
        print('\nwrong path, please use as example- c:\\traceairroot\\account\\project\\YYYY-MM-DD\n')
        continue





