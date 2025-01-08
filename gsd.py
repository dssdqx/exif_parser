
camera_specs = {
    'M3E': {'pixel_size': 0.0064,  'image_width': 5280, 'focal_length': 24},  # Модель M3E
    'M3M': {'pixel_size': 0.0064, 'image_width': 5280, 'focal_length': 24}  # Модель M3M
}



def calculate_gsd(height, model):

    specs = camera_specs[model]

    gsd = (height * specs['pixel_size']) / (specs['focal_length'])
    gsd_cm = round(gsd, 3)*100
    if gsd_cm <= 1:
        print(f'\nGSD: {round(gsd_cm, 2)} cm\naverage height (relative): {round(height, 2)} meters\nmaybe need to use thinning')
    else:
        print(f'\nGSD: {round(gsd_cm, 2)} cm\naverage height (relative): {round(height, 2)} meters')



