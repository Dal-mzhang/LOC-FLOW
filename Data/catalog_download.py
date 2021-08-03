from obspy import UTCDateTime
from obspy import read_inventory
from obspy.clients.fdsn import Client

#obspy is included in phasenet
#type 'conda activate phasenet' first
# station region
latref = 42.75 # reference lat.
lonref = 13.25 # reference lon.
maxradius = 50 # maximum radius in km.
eventprovider = "INGV" # use specfic provider, e.g., IRIS, SCEDC, INGV, etc
tbeg=UTCDateTime("2016-10-14T0:00:00.00") # beginning time
tend=UTCDateTime("2016-10-15T0:00:00.00") # ending time

# file name
eventfile = 'catalog.dat'

client = Client(eventprovider)
events = client.get_events(starttime=tbeg, endtime=tend, latitude=latref, longitude=lonref, maxradius=maxradius/111.19,orderby="time-asc")
#events.plot()

with open(eventfile, "w") as f:
    for event in events:
        origin = event.origins[0]
        f.write("{} {} {} {} {}\n".format(origin.time, origin.latitude, origin.longitude, origin.depth/1000, event.magnitudes[0].mag))
f.close()
