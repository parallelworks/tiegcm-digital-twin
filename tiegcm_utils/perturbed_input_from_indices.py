from datetime import datetime, timedelta
import os
from scipy.stats import norm, truncnorm
from tiegcm_utils.tiegcm_inputs import TGCMInput

def configure_tgcm_timestep(src_yr:int, src_day:int, src_hr:int, hr_diff:int, 
                            step:int, input_fn:str="tiegcm_res5.0.inp", 
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
    :param step: TIE-GCM internal timestep [seconds]
    :param input_fn: Input filename (optional, must be .inp)
    :param kp: Kp index (optional)
    :param f107: F10.7 index (optional)
    :param f107a: 81-day average of F10.7 (optional)

    returns: start date for the run in a string with format YYYY_ddd_HHH
    """

    # Configure date variables
    src_str = f"{src_yr}_{src_day}_{src_hr:03}"
    src_date = datetime.strptime(src_str, "%Y_%j_0%H")
    start_date = src_date + timedelta(hours=hr_diff)
    start_str = start_date.strftime("%Y_%j_0%H")
    start_year = start_date.year
    start_day = start_date.timetuple().tm_yday
    start_hour = start_date.hour
    stop_date = start_date + timedelta(hours=3)
    stop_day = stop_date.timetuple().tm_yday
    stop_hour = stop_date.hour

    # Create input file object
    # NOTE: using placeholders for Kp, F107, F107A
    # These are adjusted on a per-ensemble-member basis separately
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
        MXHIST_PRIM=12,
        MXHIST_SECH=12,
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
        OUTPUT=[f"tiegcm_primary_output_src_{src_str}.nc", f"tiegcm_primary_output_start_{start_str}.nc"],
        SECOUT=f"tiegcm_secondary_output_{start_str}.nc",
        SOURCE=None,
        SOURCE_START=None,
    )

    # Write input file
    tgcm_input.write_to_file(input_fn)

    return start_str


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

def write_inp(N_ENS:int, WORK_DIR:str, JOB_ID:str, kp:float, f107:float, f107a:float):
    # Set options
    #N_ENS = 100
    REL_STD = 0.1
    #JOB_ID = "gannon_storm_ens"
    #WORK_DIR = os.getcwd()
    TIMESTEP = 60
    SRC_YR = 2024
    SRC_DAY = 130
    SRC_HR = 21
    run_workdir = f"{WORK_DIR}/run/{JOB_ID}"

    # Generate and store relative perturbations for this run
    perturb_fn = f"{run_workdir}/ensemble_rel_perturbations.txt"
    relative_perturbations = generate_perturbations(N_ENS, REL_STD, fn=perturb_fn)

    # Configure input file    
    run_date = f"{SRC_YR}_{SRC_DAY}_{SRC_HR:03}"
    inp_fn = f"{WORK_DIR}/run/{JOB_ID}/tiegcm_res5.0_{run_date}.inp"
    hr_diff = 0  # hour offset from SRC time, can increment if looping over multiple timesteps
    run_date = configure_tgcm_timestep(SRC_YR, SRC_DAY, SRC_HR, hr_diff, TIMESTEP, inp_fn)
    kp_fn = f"{WORK_DIR}/run/{JOB_ID}/ensemble_kp_{run_date}.txt"
    f10_fn = f"{WORK_DIR}/run/{JOB_ID}/ensemble_f107_{run_date}.txt"
    perturb_drivers(kp, f107, f107a, relative_perturbations, run_workdir, 
                    kp_fn, f10_fn, inp_fn)

if __name__ == '__main__':
    # Check if the correct number of arguments is provided
    if len(sys.argv) != 6:
        print("Usage: python perturbed_input_from_indices.py N_ENS WORK_DIR JOB_ID kp f107 f107a")
        sys.exit(1)

    # Read ensemble size and other parameters from command line arguments
    N_ENS = int(sys.argv[1])
    WORK_DIR = int(sys.argv[2])
    JOB_ID = str(sys.argv[3])
    kp = float(sys.argv[4])
    f107 = float(sys.argv[5])
    f107a = float(sys.argv[6])
    
    # Create the ensemble directories
    for ii in range(1, N_ENS+1):
        my_dir=f"{WORK_DIR}/run/{JOB_ID}/{ii}"
        os.makedirs(my_dir, exist_ok = False)
    
    # Launch main function that calls other functions
    write_inp(N_ENS=N_ENS, WORK_DIR=WORK_DIR, JOB_ID=JOB_ID, kp=kp, f107=f107, f107a=f107a)
