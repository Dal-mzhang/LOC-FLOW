from csv import reader
import os, shutil, sys

'''
Choice of input format (https://github.com/smousavi05/EQTransformer):
hdf5: This option is recommended for smaller time periods (a few days to a month)
mseed: it can be more memory intensive. it is recommended when mseed fils are one 
month long or shorter.
'''


# input dataset
input = "../../Data/dataset"
# station info file
station = "../../Data/json/station_list.json"	
# output dir
output = "output"

# input data format (mseed/hdf5)
inp_format = "hdf5" 
overlap = 0.4   # amount of overlap for the sliding detection window
d_th = 0.3      # detection threshold
p_th = 0.2      # P picking threshold
s_th = 0.2      # S picking threshold


def main():
    if len(sys.argv) != 2:
        print("Usage: python run_picker.py <model>")
        print("Please provide a model (e.g., OBST/EQT) as a command-line argument.")
        sys.exit(1)  

    model = sys.argv[1]
    if model not in ["OBST", "EQT"]:
        print(f"Invalid model: {model}")
        print("Please provide a valid model (OBST or EQT).")
        sys.exit(1) 

    if model == 'OBST':
        model = f'models/OBSTransformer.h5'
    else:
        model = f'models/EqTransformer.h5'

    print(f"Running with model: {model}")



    # step 1: phase picking 
    if inp_format == "hdf5":
        from EQTransformer.utils.hdf5_maker import preprocessor

        if not os.path.isdir(f'{input}_processed_hdfs'):
            preprocessor(preproc_dir="./preproc",
                        mseed_dir=input,
                        stations_json=station, 
                        overlap=overlap,
                        n_processor=10)


        from EQTransformer.core.predictor import predictor
        predictor(input_dir=f'{input}_processed_hdfs',
                input_model=model,
                output_dir=output,
                estimate_uncertainty=False,
                output_probabilities=False,
                number_of_sampling=5,
                loss_weights=[0.02, 0.40, 0.58],
                detection_threshold=d_th,                
                P_threshold=p_th,
                S_threshold=s_th, 
                number_of_plots=0,
                plot_mode='time',
                batch_size=500,
                number_of_cpus=10,
                keepPS=False,
                spLimit=60)
        
        if os.path.isdir('preproc'):
            shutil.rmtree('preproc')
            
    else:
        from EQTransformer.core.mseed_predictor import mseed_predictor
        mseed_predictor(input_dir=input,   
            input_model=model,
            stations_json=station,
            output_dir=output,
            loss_weights=[0.02, 0.40, 0.58],
            detection_threshold=d_th, 
            P_threshold=p_th,
            S_threshold=s_th,
            number_of_plots=0,
            plot_mode='time',
            normalization_mode='std',
            batch_size=500,
            overlap=overlap,
            gpuid=None,
            gpu_limit=None)
        

    # step 2: output format conversion for pick2real program
    print('converting outputs to REAL-readable format ..')

    if os.path.isdir('picks'):
        shutil.rmtree('picks')
    os.mkdir('picks')

    pp = []
    ss = []

    for root, dirs, files in os.walk(output):
        for file in files:
            if file == 'X_prediction_results.csv':
                filepath = os.path.join(root, file)

                with open(filepath, 'r') as f:
                    lines = reader(f)
                    next(lines)
                    for line in lines:
                        sta = line[2].strip()
                        net = line[1].strip()
                        if not net:
                            net = line[0].split('_')[1]
                        ptm = line[11]
                        ppr = line[12]
                        stm = line[15]
                        spr = line[16]

                        if ptm:
                            y = ptm.split()[0].split('-')[0]
                            m = ptm.split()[0].split('-')[1]
                            d = ptm.split()[0].split('-')[2]
                            H = float(ptm.split()[1].split(':')[0])
                            M = float(ptm.split()[1].split(':')[1])
                            S = float(ptm.split()[1].split(':')[2])
                            pts = round((H * 3600) + (M * 60) + S, 2)
                            pp.append(f'{y},{m},{d},{net},{sta},1,{pts},{ppr},0\n')

                        if stm:
                            y = stm.split()[0].split('-')[0]
                            m = stm.split()[0].split('-')[1]
                            d = stm.split()[0].split('-')[2]
                            H = float(stm.split()[1].split(':')[0])
                            M = float(stm.split()[1].split(':')[1])
                            S = float(stm.split()[1].split(':')[2])
                            sts = round((H * 3600) + (M * 60) + S, 2)
                            ss.append(f'{y},{m},{d},{net},{sta},1,{sts},{spr},0\n')


    with open('picks/temp.p', 'w') as pinp:
        pinp.writelines(pp)
    with open('picks/temp.s', 'w') as sinp:
        sinp.writelines(ss)

    print(f'pick2real -Ptemp.p -Stemp.s')
    os.chdir('./picks')
    os.popen(f'pick2real -Ptemp.p -Stemp.s').read()

if __name__ == "__main__":
    main()
