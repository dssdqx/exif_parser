import subprocess
import pandas as pd
import os
from gsd import calculate_gsd, camera_specs

ExposureProgram_dict = {0: 'Not_Defined', 1: 'Manual', 2: 'Program_AE', 3: 'Aperture-priority_AE', 4: 'Shutter_speed_priority_AE',
                        5: 'Creative_(Slow speed)', 6: 'Action_(High speed)', 7: 'Portrait',
                        8: 'Landscape', 9: 'Bulb'}
                        
MeteringMode_dict = {0: 'Unknown', 1: 'Average', 2: 'Center-weighted-average', 3: 'Spot', 4: 'Multi-spot',
                     5: 'Multi-segment', 6: 'Partial', 255: 'Other'}

LightValue_dict = {0: "Unknown", 1: "Daylight", 2: "Fluorescent",
                   3: "Tungsten (Incandescent)", 4: "Flash", 9: "Fine Weather", 10: "Cloudy", 11: "Shade", 12: "Daylight Fluorescent",
                   13: "Day White Fluorescent", 14: "Cool White Fluorescent", 15: "White Fluorescent", 16: "Warm White Fluorescent",
                   17: "Standard Light A", 18: "Standard Light B", 19: "Standard Light C", 20: "D55", 21: "D65", 22: "D75", 23: "D50",
                   24: "ISO Studio Tungsten", 255: "Other"}

exif_tags = [
    "-filename",
    "-GPSLongitude",
    "-GPSLatitude",
    "-GPSAltitude",
    "-Model",
    "-ImageSize",
    "-ModifyDate",
    "-Aperture",
    "-ExposureTime",
    "-ExposureProgram",
    "-ISO",
    "-RtkFlag",
    "-ShutterType",
    "-MeteringMode",
    "-DewarpData",
    "-LightSource",
    "-NTRIPHost",
    "-NTRIPMountPoint",
    "-DigitalZoomRatio",
    "-RtkStdLon",
    "-RtkStdLat",
    "-RtkStdHgt",
    "-DroneSerialNumber",
    "-GPSXYAccuracy",
    "-GPSZAccuracy",
    "-FocusDistance",
    "-RelativeAltitude",
    "-About"
]


tab_columns = [
    "photo",
    "lon",
    "lat",
    "height",
    "model",
    "image_size",
    "created_date",
    "Aperture",
    "Exposure",
    "program",
    "iso",
    "flag",
    "shutter_type",
    "mode",
    "dewarping",
    "light_source",
    "ntrip",
    "mount_point",
    "zoom_ratio",
    "std_lon",
    "std_lat",
    "std_hgt",
    "drone_SN",
    "autel_accuracy_xy",
    "autel_accuracy_z",
    "focus_distance",
    "height_relative",
    "autel_check"
]

exif_columns = " ".join(exif_tags)

class Parser:

    def __init__(self, photos_folder, report_folder):
        self.photos_folder = photos_folder
        self.report_folder = report_folder
        #self.file_export_name = 'exif_report'

        tmp = self.report_folder.split("\\")
        self.file_export_name = tmp[-2] +  tmp[-1][8:] + tmp[-1][5:7] # baseline1412 ddmm

    def export_raw_file(self, exif_columns):
        find = f'exiftool -r {exif_columns} -T -n {self.photos_folder} > {self.photos_folder}\\out.txt'
        subprocess.run(find, shell=True, capture_output=True, text=True)


    def time_mission_groups(self, df):

        df = df.copy()
        df["created_date"] = pd.to_datetime(df["created_date"], format="%Y:%m:%d %H:%M:%S")

        df = df.sort_values("created_date")

        df["time_diff_sec"] = df["created_date"].diff().dt.total_seconds()
        df["time_diff_sec"] = df["time_diff_sec"].fillna(0.0)
        jumps = df[df["time_diff_sec"] > 20].copy()
        return len(jumps) + 1

    def read_file(self, tab_columns):     
        w_tab = pd.read_csv((f'{self.photos_folder}\\out.txt'), sep = '\t', names = tab_columns)
        os.remove(f'{self.photos_folder}\\out.txt')                                                    
        df = pd.DataFrame(w_tab)
        df = df.query("Exposure != '-' ")
        df = df.copy()
        if df.empty:
            print('no photos... return')
            return False

        df['Exposure'] = df['Exposure'].apply(lambda x: int(1 / float(x)))
        df['iso'] = df['iso'].apply(lambda x: int(x))

        df.loc[df['dewarping'] == '-', 'dewarping'] = 'on'
        df.loc[df['dewarping'] != 'on', 'dewarping'] = 'off'
        
        df.loc[df['ntrip'] == '-', 'ntrip'] = 'local base'
        df.loc[df['mount_point'] == '-', 'mount_point'] = 'none'

        self.model_values = set(df['model'])
        self.exif_check = set(df['autel_check'])  

        if df['height_relative'].ne('-').all():
            df["height_relative"] = df["height_relative"].astype(float)
        
        if len(self.model_values) == 1:
            self.model_value = list(self.model_values)[0]
             
            if self.model_value in camera_specs:
                average_height = round(df['height_relative'].mean(), 2)
                calculate_gsd(average_height, self.model_value)
        
        df = df.drop(columns=['height_relative'])

        if list(self.exif_check)[0] != 'Autel Robotics Meta Data' and len(self.exif_check) == 1:
            df = df.drop(columns=['autel_accuracy_xy'])
            df = df.drop(columns=['autel_accuracy_z'])
            df = df.drop(columns=['autel_check'])
            self.autel_check = 0
        else:
            self.autel_check = 1

        df.to_excel(f'{self.report_folder}\\{self.file_export_name}.xlsx', sheet_name='Sheet1', index = False)

        # проверяем количество миссий и кол-во групп по фокусу

        if df['focus_distance'].ne('-').all():
            focus_dict = df.groupby("focus_distance")["photo"].apply(list).to_dict()
            len_focus = len(focus_dict.keys())
            len_time_groups = self.time_mission_groups(df[['photo', 'created_date']])
            
            if len_time_groups == len_focus:
                print(f'\033[92mfocus distance groups and time groups counts ({len_focus}) match\n\033[0m')
            else:
                print(f'\033[32mThere are focus distance groups: {len_focus} and time groups: {len_time_groups}\n\033[0mUse FocusGroup first, then TimeGroup in Metashape.')


        else:
            len_time_groups = self.time_mission_groups(df[['photo', 'created_date']])
            print(f'\033[92mno exif info about focus distance; count flight missions: {len_time_groups}\n\033[0m')


        df['created_date'] = df['created_date'].apply(lambda x: x[0:10])
        df['Aperture'] = df['Aperture'].apply(lambda x: round(float(x),2)) 

        self.image_size_values = set(df['image_size'])
        self.date_values = set(df['created_date'])
        self.exposure_values = set(df['Exposure'])
        self.aperture_values = set(df['Aperture'])
        self.iso_values = set(df['iso'])
        self.rtk_values = set(df['flag'])
        self.program_values = set(df['program'])
        self.shutter_values = set(df['shutter_type'])
        self.mode_values = set(df['mode'])
        self.dewarping_values = set(df['dewarping'])
        self.light_source = set(df['light_source'])
        self.ntrip_values = set(df['ntrip'])
        self.mount_point_values = set(df['mount_point'])
        self.zoom_values = set(df['zoom_ratio'])
        self.drone_values = set(df['drone_SN'])
        self.focus_distance = set(df['focus_distance'])

        self.exposure_values_lst = list(df['Exposure'])
        self.rtk_values_lst = list(df['flag'])

        self.df = df

        self.df['program'] = self.df['program'].astype(int)
        self.program_name = []
        for q in self.program_values:
            for k, v in ExposureProgram_dict.items():
                if int(q) == k:
                    self.program_name.append(v)
                    self.df.loc[self.df['program'] == k, 'program_name'] = v
        
        self.program_value_lst = list(df['program_name'])

        for q in self.mode_values:
            for k, v in MeteringMode_dict.items():
                if int(q) == k:
                    self.metering_name = str(v)

        self.light_source_name = []
        for q in self.light_source:
            for k, v in LightValue_dict.items():
                if int(q) == k:
                    self.light_source_name.append(str(v))
        return True

    def std_report_show(self, column_name):
        self.df[column_name] = pd.to_numeric(self.df[column_name], errors='coerce')
        column = self.df[column_name]
        print(f'{column_name} max: {round(column.max(), 3)}, min: {round(column.min(), 3)}, mean: {round(column.mean(), 3)}')

    def view_report(self):
        print(f'\ncamera model: {self.model_values}\nimage size: {self.image_size_values}\nflight date(yyyy-mm-dd): {self.date_values}\n'
               f'photos: {len(self.df)}\n\naperture: {sorted(self.aperture_values)}\nshutter: {sorted(self.exposure_values)}\niso: {sorted(self.iso_values)}\n'
               f'program: {self.program_name}\ndrone SN: {self.drone_values}\nshutter type: {self.shutter_values}\nmode: {self.metering_name}\nzoom ratio mode: { self.zoom_values}\nfocus distance: {sorted(self.focus_distance)}\n'
               f'dewarping: {self.dewarping_values}\nlight source: {sorted(self.light_source_name)}\nrtk: {sorted(self.rtk_values)}\nRTK correction from: {sorted(self.ntrip_values)}\n'
               f'Mount point: {sorted(self.mount_point_values)}\n')
         
        troubles = [i for i in self.exposure_values if i < 600]
        if len(troubles) > 3:
            print(f'\nshutter values are critical minimal {sorted(troubles)} possibility BLUR - NO FOCUS \n' 
                f'need to use shutter speed priority mode with (1\\1000) value\n')
        
        for i in sorted(self.exposure_values):
            number = self.exposure_values_lst.count(i)
            pct = str(round(int(number)/int(len(self.df))*100,1))
            print(f'{i} value shutter - {number} photos, {pct}% ')

        print('\n_________________\n')

        for i in sorted(self.rtk_values):
            number_flag = self.rtk_values_lst.count(i)
            pct2 = str(round(int(number_flag)/int(len(self.rtk_values_lst))*100,1))
            print(f'{i} value rtk flag - {number_flag} photos, {pct2}%')

        is_rtk_flag = self.df['flag'].eq('-').all()
        is_rtk_flag2 = self.df['flag'].eq('0').all()
        is_rtk_flag3 = self.df['flag'].eq('50').all()

        if is_rtk_flag == True and self.model_value != 'XL705':
            print('\nthis is not RTK flight, but it could be a PPK flight')
        if is_rtk_flag2 == True and self.model_value != 'XL705':
            print('\nthis is not a RTK flight')
        if is_rtk_flag3 == True:
            print('\nthis is a good RTK flight with high accuracy')
            #self.df.to_csv(f'{self.report_folder}\\scan.photo.georef.txt', sep='\t', columns=["photo", "lon", "lat", "height"], index=False) 
        

        if len(self.program_name) >= 2:
            print('\n')
            print(f'carefully, {len(self.program_name)} types of shooting modes were used:\n')
            for i in sorted(self.program_name):
                number_values = self.program_value_lst.count(i)
                pct = str(round(int(number_values)/int(len(self.df))*100,1))
                print(f'{i} - {number_values} photos, {pct}%')


        unique_count = self.df['flag'].nunique()
        if unique_count > 1:
            self.df.loc[self.df['flag'] == '50', 'accuracy'] = 0.05
            self.df.loc[self.df['flag'] != '50', 'accuracy'] = 0.30
            print(f'\nprepared file {self.report_folder}\\scan.photo.georef.txt\nwith field accuracy for each photo')
            self.df.to_csv(f'{self.report_folder}\\scan.photo.georef.txt', sep='\t', columns=["photo", "lon", "lat", "height", 'accuracy'], index=False) 

        print('\n_________________\n')

        is_rtk = self.df['std_lon'].ne('-').all()
        if is_rtk == True:
            self.std_report_show('std_lon')
            self.std_report_show('std_lat')
            self.std_report_show('std_hgt')
            print('_________________\n')


        if self.autel_check == 1:
            self.df.loc[:, 'std_lon'] = self.df['autel_accuracy_xy']
            self.df.loc[:, 'std_lat'] = self.df['autel_accuracy_xy']
            self.df.loc[:, 'std_hgt'] = self.df['autel_accuracy_z']
            print(f'this is a Autel Robotics UAV\n\nprepared file {self.report_folder}\\scan.photo.georef.txt\nwith field accuracy for each photo\n')
            self.df.to_csv(f'{self.report_folder}\\scan.photo.georef.txt', sep='\t', columns=["photo", "lon", "lat", "height", 'autel_accuracy_xy', 'autel_accuracy_z'], index=False, header=False) 

            self.std_report_show('std_lon')
            self.std_report_show('std_lat')
            self.std_report_show('std_hgt')
            print('_________________\n')

        if len(self.dewarping_values) > 1:
            print(f'carefully! Within the flight, dewarping mode on\\off\n' 
                  f're-alignment with groups dewarping mode in Metashape')

        if len(self.drone_values) > 1:
            print(f'carefully! {len(self.drone_values)} drones were used during the capture.\n' 
                  f'please be aware, chunks processing may be required in Metashape')

        print(f'\nthe detailed information can be found in the XLSX file here:\n{self.report_folder}\\{self.file_export_name}.xlsx\n')


print('based on ExifTool version 12.60 (https://exiftool.org)')
print('exif_parser version: 1.2\n')


if __name__ == "__main__":

    u_input = input(r'folder with photos: ')

    if '"' in u_input:
        u_input = u_input.replace('"', '')
        
    #photos_folder = os.path.join(os.path.normpath(u_input))
    photos_folder = os.path.normpath(u_input)
    report_folder = os.path.normpath(u_input)

    task = Parser(photos_folder, report_folder)
    task.export_raw_file(exif_columns)
    if task.read_file(tab_columns):
        task.view_report()

