from datetime import datetime, timedelta
import os
import sys
from scipy.stats import norm, truncnorm
from tiegcm_inputs import TGCMInput
from fetch_indices import get_f107
from fetch_indices import get_kp_array

def configure_tgcm_timestep(src_yr:int, src_day:int, src_hr:int, hr_diff:int, hr_sim:int,
                            step:int, start_type:str, input_fn:str="tiegcm_res5.0.inp", 
                            kp:float=3., f107:float=90., f107a:float=90.) -> str:
    """
    Write the TIE-GCM input file for a 3-hour run given the source time (for 
    filename containing timestep before entire run), offset from source time, 
    and internal timestep for the model. Input filename can be specified if 
    different from default. Kp and F10.7 indices are optional given that they 
    are overridden when generating an ensemble; placeholders are used if they 
    are not provided.

    :param src_yr: year of source file
    :param src_day: day of year of source file
    :param src_hr: hour of day of source file
    :param hr_diff: hour offset from source file
    :param hr_sim: hour duration of simulation
    :param step: TIE-GCM internal timestep [seconds]
    :param input_fn: Input filename (optional, must be .inp)
    :param kp: Kp index (optional)
    :param f107: F10.7 index (optional)
    :param f107a: 81-day average of F10.7 (optional)

    returns: start date for the run in a string with format YYYY_ddd_HHH
    """

    # Configure date variables
    src_str = f"{src_yr}_{src_day:03}_{src_hr:03}"
    src_date = datetime.strptime(src_str, "%Y_%j_0%H")
    start_date = src_date + timedelta(hours=hr_diff)
    start_str = start_date.strftime("%Y_%j_0%H")
    start_year = start_date.year
    start_day = start_date.timetuple().tm_yday
    start_hour = start_date.hour
    stop_date = start_date + timedelta(hours=hr_sim)
    stop_day = stop_date.timetuple().tm_yday
    stop_hour = stop_date.hour

    # Create input file object differently for start type
    # `cold` start: SOURCE is initial condition file, only one file listed in OUTPUT
    # `warm` start: SOURCE=None, OUTPUT=[src_file, out_file]
    if (start_type == "cold"):
        tgcm_input = TGCMInput(            
            AURORA=True,
            CALC_HELIUM=True,
            COLFAC=1.5,
            CALENDAR_ADVANCE=True,
            CURRENT_KQ=False,
            CURRENT_PG=True,
            DYNAMO=True,
            F107=f107,
            F107A=f107a,
            GSWM_MI_DI_NCFILE="$TGCMDATA/gswm_diurn_5.0d_99km.nc",
            GSWM_MI_SDI_NCFILE="$TGCMDATA/gswm_semi_5.0d_99km.nc",
            HIST=(0, 0, 15),
            LABEL="tiegcm res=5.0",
            MXHIST_PRIM=200,
            MXHIST_SECH=200,
            KP=kp,
            POTENTIAL_MODEL="HEELIS",
            SECFLDS=[
                'TN','UN','VN','WN','O2','O1','N2','NO','N4S','HE','NE','TE','TI','TEC',
                'O2P','OP','POTEN','UI_ExB','VI_ExB','WI_ExB','DEN','QJOULE','HMF2',
                'NMF2','Z','ZG'
            ],
            SECHIST=(0, 0, 15),
            SECSTART=(start_day, start_hour, 15),
            SECSTOP=(stop_day, stop_hour, 0),
            START=(start_day, start_hour, 0),
            START_DAY=start_day,
            START_YEAR=start_year,
            STEP=step,
            STOP=(stop_day, stop_hour, 0),
            OUTPUT=f"tiegcm_primary_output_{start_str}.nc",
            SECOUT=f"tiegcm_secondary_output_{start_str}.nc",
            SOURCE=f"tiegcm_primary_src_{src_str}.nc",
            SOURCE_START=(start_day, start_hour, 0) # Required if using SOURCE e.g. (80, 0, 0)
        )
        end_message="Wrote cold start namelist."
    elif (start_type == "warm"):
        tgcm_input = TGCMInput(
            AURORA=True,
            CALC_HELIUM=True,
            COLFAC=1.5,
            CALENDAR_ADVANCE=True,
            CURRENT_KQ=False,
            CURRENT_PG=True,
            DYNAMO=True,
            F107=f107,
            F107A=f107a,
            GSWM_MI_DI_NCFILE="$TGCMDATA/gswm_diurn_5.0d_99km.nc",
            GSWM_MI_SDI_NCFILE="$TGCMDATA/gswm_semi_5.0d_99km.nc",
            HIST=(0, 0, 15),
            LABEL="tiegcm res=5.0",
            MXHIST_PRIM=200,
            MXHIST_SECH=200,
            KP=kp,
            POTENTIAL_MODEL="HEELIS",
            SECFLDS=[
                'TN','UN','VN','WN','O2','O1','N2','NO','N4S','HE','NE','TE','TI','TEC',
                'O2P','OP','POTEN','UI_ExB','VI_ExB','WI_ExB','DEN','QJOULE','HMF2',
                'NMF2','Z','ZG'
            ],
            SECHIST=(0, 0, 15),
            SECSTART=(start_day, start_hour, 15),
            SECSTOP=(stop_day, stop_hour, 0),
            START=(start_day, start_hour, 0),
            START_DAY=start_day,
            START_YEAR=start_year,
            STEP=step,
            STOP=(stop_day, stop_hour, 0),
            OUTPUT=[f"tiegcm_primary_src_{src_str}.nc", f"tiegcm_primary_output_start_{start_str}.nc"],
            SECOUT=f"tiegcm_secondary_output_{start_str}.nc",
            SOURCE=None,
            SOURCE_START=None,
        )
        end_message="Wrote warm start namelist."
    else:
        end_message="ERROR! You must pick either a `cold` or `warm` start_type!"
        
    # Write input file
    tgcm_input.write_to_file(input_fn)

    return end_message

def generate_perturbations(n_ens:int, std:float, mean:float=1., range:float=None,
                           fn:str="ensemble_rel_perturbations.txt") -> list[float]:
    """
    Generate perturbations for inputs to an ensemble of size n_ens of models, 
    using a Gaussian distribution with the provided mean and standard deviation. 
    Can optionally be truncated using the range (max deviation from the mean). 
    Default mean is 1 for fractional perturbations. Writes ensemble 
    perturbations to a text file (option to specify non-default filename) and 
    also returns them in a list.

    :param n_ens: size of ensemble
    :param std: standard deviation of Gaussian distribution to be sampled
    :param mean: mean of Gaussian distribution to be sampled (optional, default 1)
    :param range: maximum deviation from the mean (optional)
    :param fn: filename at which to save perturbations (optional)

    returns: list of ensemble perturbations (size n_ens)
    """

    # Sample and truncate if necessary
    if range == None:
        perturbations = norm.rvs(size=n_ens, scale=std, loc=mean)
    else:
        a = -range/std
        b = range/std
        perturbations = truncnorm(a, b, loc=mean, scale=std).rvs(size=n_ens)
    print(f"Generated ensemble perturbations!")

    # Write file
    print(f"Writing ensemble perturbations to {fn}")
    with open(fn, "w") as f:
        for p in perturbations: f.write(f"{p}\n")

    return perturbations.tolist()


def perturb_drivers(kp_mean:float, f107_mean:float, f107a:float,
                    relative_perturbations:list[float], run_workdir:str,
                    kp_fn:str="ensemble_kp.txt", f10_fn:str="ensemble_f107.txt",
                    input_fn:str="tiegcm_res5.0.inp"):
    """
    Generate perturbed Kp/F10.7 indices for the ensemble given mean indices and 
    a relative perturbation array for the run time. Writes two text files in the 
    run directory containing the ensemble values of Kp and F10.7, and modifies 
    the .inp file for each ensemble member with the corresponding indices. 
    Option to specify non-default filenames for each of the above.
    NOTE: F10.7 file contains F10.7A at the end

    :param kp_mean: mean Kp index for the run time
    :param f107_mean: mean F10.7 index for the run time
    :param f107a: 81-day averaged F10.7 for the run time (not perturbed)
    :param relative_perturbations: relative (fractional) perturbations on mean 
                                   indices for ensemble, list of size N_ENS
    :param run_workdir: directory in which to put ensemble .inp files for run
    :param kp_fn: filename for ensemble Kp (optional)
    :param f107_fn: filename for ensemble F10.7 (optional)
    :param input_fn: input filename (optional, must be .inp)
    """

    # Generate Kp ensemble
    kps = [kp_mean * p for p in relative_perturbations]
    print(f"Writing ensemble Kp to {kp_fn}")
    with open(kp_fn, "w") as f:
        for kp in kps: f.write(f"{kp}\n")

    # Generate F10.7 ensemble
    f10s = [f107_mean * p for p in relative_perturbations]
    print(f"Writing ensemble F10.7 to {f10_fn}")
    with open(f10_fn, "w") as f:
        for f10 in f10s: f.write(f"{f10}\n")
        f.write(f"{f107a}\n")

    # Get existing parameters
    with open(input_fn, "r") as f:
        input_lines = f.readlines()

    # Write input file for each ensemble member
    for i in range(len(relative_perturbations)):
        ens_fn = f"{run_workdir}/mem{(i+1):03}/{os.path.basename(input_fn)}"
        with open(ens_fn, "w") as f:
            for line in input_lines:
                if "F107 " in line:
                    f.write(f"    F107 = {f10s[i]}\n")
                elif "F107A " in line:
                    f.write(f"    F107A = {f107a}\n")
                elif "KP " in line:
                    f.write(f"    KP = {kps[i]}\n")
                else:
                    f.write(line)

def write_inp(N_ENS:int, WORK_DIR:str, JOB_ID:str, SRC_YR:int, SRC_DAY:int, SRC_HR:int, HR_DIFF:int, HR_SIM:int, TIMESTEP:int, start_type:str, kp:float, f107:float, f107a:float):
    # Set options
    #N_ENS = 100
    REL_STD = 0.1
    #JOB_ID = "gannon_storm_ens"
    #WORK_DIR = os.getcwd()
    #TIMESTEP = 60
    #SRC_YR = 2024
    #SRC_DAY = 130
    #SRC_HR = 21
    run_workdir = f"{WORK_DIR}/run/{JOB_ID}"
    
    # This is the first time step of output to report
    # (i.e. simulation fast forwards to this hour diff
    # wrt the initialization time in the src time)
    #hr_diff = 0  # hour offset from SRC time, can increment if looping over multiple timesteps
    
    # This the duration of the simulation
    #HR_SIM=24

    # Generate and store relative perturbations for this run
    perturb_fn = f"{run_workdir}/ensemble_rel_perturbations.txt"
    relative_perturbations = generate_perturbations(N_ENS, REL_STD, fn=perturb_fn)

    # Configure input file    
    run_date = f"{SRC_YR}_{SRC_DAY:03}_{SRC_HR:03}"
    inp_fn = f"{WORK_DIR}/run/{JOB_ID}/tiegcm_res5.0_{run_date}.inp"
    run_date = configure_tgcm_timestep(SRC_YR, SRC_DAY, SRC_HR, HR_DIFF, HR_SIM, TIMESTEP, start_type, inp_fn)
    kp_fn = f"{WORK_DIR}/run/{JOB_ID}/ensemble_kp_{run_date}.txt"
    f10_fn = f"{WORK_DIR}/run/{JOB_ID}/ensemble_f107_{run_date}.txt"
    perturb_drivers(kp, f107, f107a, relative_perturbations, run_workdir, 
                    kp_fn, f10_fn, inp_fn)

if __name__ == '__main__':
    # Check if the correct number of arguments is provided
    # Typical command line call:
    # python tiegcm_utils/perturbed_input_from_indices.py {ens_size} {work_dir} {runid} {datetime_str} {simulation_hours} {start_type} {src_file}
    if len(sys.argv) < 8:
        print("Usage: python perturbed_input_from_indices.py N_ENS WORK_DIR JOB_ID datetime_str simulation_hours start_type src_file")
        sys.exit(1)
    #==============================================
    # Read ensemble size and other parameters from 
    # command line arguments
    #==============================================
    # Where and shape
    N_ENS = int(sys.argv[1])
    WORK_DIR = str(sys.argv[2])
    JOB_ID = str(sys.argv[3])
    
    # Date/time info - based on the date string
    datetime_str=str(sys.argv[4])
    #SRC_YR = str(sys.argv[4])
    #SRC_DAY = int(sys.argv[5])
    #SRC_HR = int(sys.argv[6])
    
    # Hardcoded?
    HR_DIFF = 0
    TIMESTEP = 60
    
    HR_SIM = int(sys.argv[5])
    start_type = str(sys.argv[6])
    src_file = str(sys.argv[7])
    
    # Solar params - computed on the fly below
    #kp = float(sys.argv[8])
    #f107 = float(sys.argv[9])
    #f107a = float(sys.argv[10])

    print("Starting perturbed_input_from_indices with:")
    print("N_ENS: "+str(N_ENS))
    print("WORK_DIR: "+WORK_DIR)
    print("JOB_ID: "+JOB_ID)
    print("datetime_str: "+datetime_str)
    print("HR_DIFF: "+str(HR_DIFF))
    print("TIMESTEP: "+str(TIMESTEP))
    print("HR_SIM: "+str(HR_SIM))
    print("start_type: "+start_type)
    print("src_file: "+src_file)
    
    print("Start working on intermediate values...")
    
    #==============================================
    # Date information
    #==============================================
    dt = datetime.strptime(datetime_str, '%Y/%m/%d/%H:%M:%S')
    SRC_YR = int(dt.strftime('%Y'))
    SRC_DAY = int(dt.strftime('%j'))
    SRC_HR = int(dt.strftime('%H'))
    
    # For initial conditions file naming
    src_str = f"{SRC_YR}_{SRC_DAY:03}_{SRC_HR:03}"
    
    print("datetime_str converted to Y-D-H: "+src_str)
    
    #==============================================
    # Get solar forcing
    #==============================================
    (f107, f107a) = get_f107(dt)
    
    print("Solar forcing f107: "+str(f107))
    print("Solar forcing f107a: "+str(f107a))    
    
    kp_array = get_kp_array(dt)
    # We only want the last value in the Kp array
    kp=kp_array[-1]
    
    print("Solar forcing Kp: "+str(kp))
    
    #==============================================
    # Create the ensemble directories
    #==============================================
    print("Creating ensemble dirs...")
    for ii in range(1, N_ENS+1):
        my_dir=f"{WORK_DIR}/run/{JOB_ID}/mem{(ii):03}"
        os.makedirs(my_dir, exist_ok = False)
    
        # Change the path to this file for different initial
        # conditions. The file name it is being copied to
        # must match the first entry on in the SOURCE
        # or OUTPUT parameter on the namelist (.inp) in 
        # configure_tgcm_timestep, above.
        os.system(f"cp {WORK_DIR}/{src_file} {my_dir}/tiegcm_primary_src_{src_str}.nc")
        
    #==============================================
    # Launch main function that calls other functions
    #==============================================
    print("Calling write_inp to make namelists...")
    write_inp(
        N_ENS=N_ENS, 
        WORK_DIR=WORK_DIR, 
        JOB_ID=JOB_ID, 
        SRC_YR = SRC_YR,
        SRC_DAY = SRC_DAY,
        SRC_HR = SRC_HR,
        HR_DIFF = HR_DIFF,
        HR_SIM = HR_SIM,
        TIMESTEP = TIMESTEP,
        start_type = start_type,
        kp=kp, 
        f107=f107, 
        f107a=f107a)
    
    print("Done!")
