import math
import obspy.taup
import numpy as ny
import sys
from obspy.taup import TauPyModel
from obspy.taup.taup_create import build_taup_model
build_taup_model("mymodel.nd") 
# when you prepare the model, please consider interpolating 
# the velocity model above the majority of seismicity (e.g., a few km/layer)
# so that VELEST (mode=0) can update it
# TauP, velest, and hypoinverse don't like low velocity layers...
model = TauPyModel(model="mymodel")

dist=1.4 #dist range in deg.
dep=20 #depth in km

ddist=0.01 #dist interval, be exactly divided by dist
ddep=1 #depth interval, be exactly divided by dep

ndep=int(dep/ddep)+1
ndist=int(dist/ddist)+1

with open("ttdb.txt", "w") as f:
    #f.write("dist dep tp ts tp_slowness ts_slowness tp_hslowness ts_hslowness p_elvecorr s_elvecorr\n")
    for idep in range(0,ndep,1): # in depth
        for idist in range(1,ndist,1): # in horizontal
            dist = idist*ddist
            dep = idep*ddep
            print(dep,dist)
            arrivals = model.get_travel_times(source_depth_in_km=dep, distance_in_degree=dist, phase_list=["P","p","S","s"])
            #print(arrivals)
            i = 0
            pi = 0
            si = 0
            while(i<len(arrivals)):
                arr = arrivals[i]
                i = i + 1
                if((arr.name == 'P' or arr.name == 'p') and pi == 0):
                    pname = arr.name
                    p_time = arr.time
                    p_ray_param = arr.ray_param*2*ny.pi/360
                    p_hslowness = -1*(p_ray_param/111.19)/math.tan(arr.takeoff_angle*math.pi/180)
                    pi = 1

                if((arr.name == 'S' or arr.name == 's') and si == 0):
                    sname = arr.name
                    s_time = arr.time
                    s_ray_param = arr.ray_param*2*ny.pi/360
                    s_hslowness = -1*(s_ray_param/111.19)/math.tan(arr.takeoff_angle*math.pi/180)
                    si = 1
                if(pi == 1 and si == 1):
                    break

            if(pi == 0 or si == 0):
                sys.exit("Error, no P or S traveltime, most likely low velocity issue: dist=%.2f, dep=%.2f, tp=%.2f, ts=%.2f" % (dist,dep,p_time,s_time))
                    
            f.write("{} {} {} {} {} {} {} {} {} {}\n".format(dist, dep, p_time,s_time, p_ray_param, s_ray_param, p_hslowness, s_hslowness, pname, sname))
