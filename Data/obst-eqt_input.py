from EQTransformer.utils.downloader import makeStationList, downloadMseeds, downloadSacs
from obspy import read
from tqdm import tqdm
import json
import os
import shutil
import glob


'''
1- You need to be in OBST/EQT environment to be able to run this code.
2- Both pickers work best on data at 100 Hz sampling rate.
3- The choice of filtering is model dependent; recommended ranges are:
OBST: 3-20 Hz
EQT: 1-45 Hz
4- Download length can't be less than 1 day.
'''

# output directory
output_dir = "dataset"
# temporal setting (download length can't be less than 1 day!)
starttime="2016-10-14 00:00:00.00"
endtime="2016-10-15 00:00:00.00"
# spatial setting
minlat=42.30
maxlat=43.20
minlon=12.64
maxlon=13.86
# download setting
clients = ["IRIS", "INGV"]
networks = "IV,YR"
networks_skip = []   # avoid these networks
stations = "*"          # e.g., "ED17,SMA1,ED18" (not a python list!)
stations_skip = []   # avoid these stations
#stations_skip = ["LNSS", "MF5", "MNTT", "SAP2"]   # avoid these stations
locations = "*"
channels = "HH?,EH?"

# preprocessing setting (filtering, trimming, ..)
f1 = 3      # lower corner for filtering (Hz)
f2 = 20     # upper corner for filtering (Hz)
sr = 100    # sampling rate (Hz)


json_basepath = os.path.join(os.getcwd(),"json/station_list.json")
if os.path.isdir(json_basepath):
    shutil.rmtree(json_basepath)
if os.path.isdir(output_dir):
    shutil.rmtree(output_dir)
    
makeStationList(json_path=json_basepath,
                  client_list=clients,
                  min_lat=minlat,
                  max_lat=maxlat,
                  min_lon=minlon, 
                  max_lon=maxlon, 
                  network=networks,
                  station=stations,
                  filter_network=networks_skip,
                  filter_station=stations_skip,
                  location=locations,
                  channel=channels,                      
                  start_time=starttime, 
                  end_time=endtime)

downloadMseeds(client_list=clients, 
        stations_json=json_basepath, 
        output_dir=output_dir, 
        start_time=starttime, 
        end_time=endtime, 
        min_lat=minlat, 
        max_lat=maxlat, 
        min_lon=minlon, 
        max_lon=maxlon,
        chunk_size=1,
        channel_list=[],
        n_processor=8)


# Preprocessing
num = len(glob.glob(f"{output_dir}/**/*.mseed", recursive=True))
prog = tqdm(total=num)
for root, _, files in os.walk(output_dir):
    for data in files:
        if data.endswith('.mseed'):
            print(data)
            datapath = os.path.join(root, data)
            st = read(datapath)
            st.merge(method=1, fill_value='interpolate')
            st.detrend("demean")
            st.detrend("linear")
            st.filter('bandpass', freqmin=f1, freqmax=f2, zerophase=True)
            st.taper(max_percentage=0.001)
            st.interpolate(sampling_rate=sr, startime=0)
            st.write(datapath, format="MSEED")
            prog.update()

# Create station info file for REAL
with open('./json/station_list.json', 'r') as js:
    data = json.load(js)

with open('station.dat', 'w') as output_file:
    for sta, info in data.items():
        net = info['network']
        lon = info['coords'][1]
        lat = info['coords'][0]
        channel = info['channels'][0][:-1]
        elevation = round(float(info['coords'][2]) / 1000, 3)

        output_file.write(f"{lon} {lat} {net} {sta} {channel} {elevation}\n")
