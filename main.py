import subprocess
import pandas as pd
import os

ExposureProgram_dict = {0: 'Not_Defined', 1: 'Manual', 2: 'Program_AE', 3: 'Aperture-priority_AE', 4: 'Shutter_speed_priority_AE',
                        5: 'Creative_(Slow speed)', 6: 'Action_(High speed)', 7: 'Portrait',
                        8: 'Landscape', 9: 'Bulb'}
MeteringMode_dict = {0: 'Unknown', 1: 'Average', 2: 'Center-weighted-average', 3: 'Spot', 4: 'Multi-spot',
                     5: 'Multi-segment', 6: 'Partial', 255: 'Other'}

exif_tags = [
    "-filename",
    "-GPSLongitude",
    "-GPSLatitude",
    "-GPSAltitude",
    "-Model",
    "-ImageSize",
    "-CreateDate",
    "-Aperture",
    "-ExposureTime",
    "-ExposureProgram",
    "-ISO",
    "-RtkFlag",
    "-ShutterType",
    "-MeteringMode",
    "-DewarpData",
    "-NTRIPHost",
    "-NTRIPMountPoint",
    "-DigitalZoomRatio",
    "-RtkStdLon",
    "-RtkStdLat",
    "-RtkStdHgt",
    "-DroneSerialNumber"
]


tab_columns = [
    "photo",
    "lon",
    "lat",
    "height",
    "model",
    "image_size",
    "create_date",
    "Aperture",
    "Exposure",
    "program",
    "iso",
    "flag",
    "shutter",
    "mode",
    "dewarping",
    "ntrip",
    "mount_point",
    "zoom_ratio",
    "std_lon",
    "std_lat",
    "std_hgt",
    "drone_SN"
]

exif_columns = " ".join(exif_tags)

class Parcer:

    def __init__(self, photos_folder, report_folder):
        self.photos_folder = photos_folder
        self.report_folder = report_folder



    def export_raw_file(self, exif_columns):
        find = f'exiftool -r {exif_columns} -T -n {self.photos_folder} > {self.photos_folder}out.txt'
        subprocess.run(find, shell=True, capture_output=True, text=True)
 

        
    def read_file(self, tab_columns):     
        w_tab = pd.read_csv((f'{self.photos_folder}out.txt'), sep = '\t', names = tab_columns)
        os.remove(f'{self.photos_folder}out.txt')                                                    
        df = pd.DataFrame(w_tab)
        df = df.query("Exposure != '-' ")
        
        df = df.copy()

        df['Exposure'] = df['Exposure'].apply(lambda x: int(1 / float(x)))

        df.loc[df['dewarping'] == '-', 'dewarping'] = 'on'
        df.loc[df['dewarping'] != 'on', 'dewarping'] = 'off'


        df.loc[df['ntrip'] == '-', 'ntrip'] = 'local base'
        df.loc[df['mount_point'] == '-', 'mount_point'] = 'None'

        df.to_excel(f'{self.report_folder}\\report.xlsx', sheet_name='Sheet1', index = False)

        df['create_date'] = df['create_date'].apply(lambda x: x[0:10])

        self.model_values = set(df['model'])
        self.image_size_values = set(df['image_size'])
        self.date_values = set(df['create_date'])
        self.exposure_values = set(df['Exposure'])
        self.aperture_values = set(df['Aperture'])
        self.iso_values = set(df['iso'])
        self.rtk_values = set(df['flag'])
        self.program_values = set(df['program'])
        self.shutter_values = set(df['shutter'])
        self.mode_values = set(df['mode'])
        self.dewarping_values = set(df['dewarping'])
        self.ntrip_values = set(df['ntrip'])
        self.mount_point_values = set(df['mount_point'])
        self.zoom_values = set(df['zoom_ratio'])
        self.drone_values = set(df['drone_SN'])

        self.exposure_values_lst = list(df['Exposure'])
        self.rtk_values_lst = list(df['flag'])

        self.df = df

        for q in self.program_values:
            for k, v in ExposureProgram_dict.items():
                if int(q) == k:
                    self.program_name = str(v)

        for q in self.mode_values:
            for k, v in MeteringMode_dict.items():
                if int(q) == k:
                    self.metering_name = str(v)



    def std_report_show(self, column_name):
        self.df[column_name] = pd.to_numeric(self.df[column_name], errors='coerce')
        column = self.df[column_name]
        print(f'{column_name} max: {round(column.max(), 3)}, min: {round(column.min(), 3)}, mean: {round(column.mean(), 3)}')

    def view_report(self):
        print(f'\ncamera model: {self.model_values}\nimage size: {self.image_size_values}\nflight date(yyyy-mm-dd): {self.date_values}\n'
               f'photos: {len(self.df)}\n\naperture: {sorted(self.aperture_values)}\nshutter: {sorted(self.exposure_values)}\niso: {sorted(self.iso_values)}\n'
               f'program: {self.program_name}\ndrone SN: {self.drone_values}\nshutter: {self.shutter_values}\nmode: {self.metering_name}\nzoom ratio mode: { self.zoom_values}\n'
               f'dewarping: {self.dewarping_values}\nrtk: {sorted(self.rtk_values)}\nRTK correction from: {sorted(self.ntrip_values)}\n'
               f'Mount point: {sorted(self.mount_point_values)}\n')
         
        troubles = [i for i in self.exposure_values if i < 600]
        if len(troubles) > 3:
            print(f'\nshutter values are critical minimal {sorted(troubles)} possibility BLUR - NO FOCUS \nneed to use' 
                f'shutter speed priority mode with (1\\1000) value\n')

        
        for i in sorted(self.exposure_values):
            number = self.exposure_values_lst.count(i)
            pct = str(round(int(number)/int(len(self.df))*100,1))
            print(f'{i} value shutter - {number} photos, {pct}% ')

        print('\n_________________\n')

        for i in sorted(self.rtk_values):
            number_flag = self.rtk_values_lst.count(i)
            pct2 = str(round(int(number_flag)/int(len(self.rtk_values_lst))*100,1))
            print(f'{i} value rtk flag - {number_flag} photos, {pct2}%')

        print('\n_________________\n')

        is_rtk = self.df['std_lon'].ne('-').all()
        if is_rtk == True:
            self.std_report_show('std_lon')
            self.std_report_show('std_lat')
            self.std_report_show('std_hgt')
            print('_________________\n')

        print(f'\nThe detailed information can be found in the XLSX file here:\n{self.report_folder}\\out.xlsx\n')

    def message(self):
        pass

    def export(self):
        pass



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
    report_folder = os.path.normpath(u_input)
    try:
        task = Parcer(photos_folder, report_folder)
        task.export_raw_file(exif_columns)
        task.read_file(tab_columns)
        task.view_report()
        print('\nnext folder...\n')
    except FileNotFoundError:
        print('\nwrong path, try again\n')
        continue

