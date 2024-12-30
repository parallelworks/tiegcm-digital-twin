from datetime import datetime, timedelta
import numpy as np
import requests

# def get_f107_avg(last_three):
#     """
#     F10.7 90-day mean is only reported in one of the three data packages each day
#     This searches the last three elements of the json and finds the one with data

#     Parameters:
#         last_three - array of last three F10.7 data packages from the SWPC json

#     Returns:
#         last reported 90-day mean of F10.7
#         corresponding observed F10.7 value
#     """
#     for data in last_three:
#         if data['ninety_day_mean']:
#             return data['ninety_day_mean'], data['flux']

# def get_forcing_today(year, day, hour, kp_url, f10_url):
#     """
#     Get Kp and F10.7 from SWPC for the current day.

#     Parameters:
#         year - current year
#         day - current day of year
#         hour - hour of desired model start

#     Returns:
#         list of lists with forcing data for the current day
#             [year, day, hour, kp, f107, f107a]
#     """
#     all_forcing = []
#     # get Kp data from SWPC
#     kp_resp = requests.get(kp_url)
#     kp_txt = kp_resp.content
#     # get F10.7 data from SWPC
#     f10_json = json.loads(urlopen(f10_url).read().decode('utf-8'))
#     # find last reported F10.7 average and corresponding observed value (will be within a day)
#     f107a, f107 = get_f107_avg(f10_json[0:3])
#     # last line of Kp txt file is the current day, split string to get data values
#     kp_today = kp_txt.splitlines()[-1].decode('utf-8')
#     kp_today_data = [x for x in kp_today.split(' ') if x][-8:]
#     for h in range(0, 24, 3):
#         if h <= hour:
#             kp = float(kp_today_data[h//3])
#             if kp < 0:
#                 print(f"Found invalid Kp for day {day} hour {h}, ignoring data")
#                 continue
#             all_forcing.append([year, day, h, kp, f107, f107a])
#     return list(reversed(all_forcing))

def get_f107(dt:datetime) -> tuple[float, float]:
    """
    Get F10.7 and F10.7A (81-day average) for the day of interest from GFZ.
    """
    # get line with data for time of interest
    line, last_81_lines = find_day(dt, last_81=True)
    # parse out F10.7 and go through last 81 days to get F10.7A
    f107 = float(line[-16:-11])
    f107a_vals = [float(l[-16:-11]) for l in last_81_lines]
    f107a = np.mean(f107a_vals)
    # make sure the grabbed values are valid
    if f107 < 0 or f107a < 0:
        raise RuntimeError(f'One or more drivers are invalid. Got F10.7={f107}, F10.7a={f107a}')
    return f107, f107a

def get_kp_array(dt:datetime) -> list[float]:
    """
    Get Kp array for the time of interest (all day until that time) from GFZ.
    """
    # get line with data for time of interest
    line = find_day(dt)
    # parse out Kp for the day until the start time
    kp_array = []
    # Add special check for hour 00 (midnight + 59 minutes)
    if ( dt.hour == 0 ):
        kp_start = 34
        kp_array.append(float(line[kp_start:kp_start+5]))
    else:
        for h in range(0, dt.hour, 3):
            kp_start = 34 + 7*(h//3)
            kp_array.append(float(line[kp_start:kp_start+5]))
    # make sure the grabbed values are valid
    if kp_array == [] or any(kp < 0 for kp in kp_array):
        raise RuntimeError(f'One or more Kp values for the requested time are invalid. Got {kp_array}')
    return kp_array

def find_day(dt:datetime, last_81:bool=False) -> str:
    """
    Find the line in the historical solar/geomag indices file that corresponds 
    to the desired day, and return it as a string for parsing.
    """
    url = "https://kp.gfz-potsdam.de/app/files/Kp_ap_Ap_SN_F107_since_1932.txt"
    resp = requests.get(url)
    lines = resp.content.splitlines()
    for i, line in enumerate(reversed(lines)):
        # get day of year from y/m/d format
        ymd_string = line[:10].decode()
        y = int(ymd_string[:4])
        m = int(ymd_string[5:7])
        d = int(ymd_string[8:10])
        # doy = datetime(y, m, d).timetuple().tm_yday
        if datetime(y, m, d) == datetime(dt.year, dt.month, dt.day):
            if not last_81:
                return line
            else:
                return line, lines[-(i+81):-i]
        if datetime(y, m, d) < datetime(dt.year, dt.month, dt.day):
            raise ValueError(f"Could not find data for {dt}")
