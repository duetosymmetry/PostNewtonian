import scri
from PYPostNewtonian.Code import PNEvolution1
from PYPostNewtonian.Code import PNWaveformModes
from PYPostNewtonian.Code import PNPsiMModes
import numpy as np
import quaternionic
import quaternion
import sxs

def PNWaveform(q,M,omega_0,chi1_0,chi2_0,frame_0,t_0=0.0, t_PNStart=False, t_PNEnd=False, datatype="h", return_chi=False, PNEvolutionOrder=4.0, PNWaveformModeOrder=3.5, TaylorTn=1, StepsPerOrbit=32, ForwardInTime=True, tol=1e-10, MinStep=1e-7):
    """
    q = m1/m2, float number,
    M = m1+m2, float number,
    omega_0: magnititude of angular velocity at t_0, float number,
    chi1_0 and chi2_0: spin vectors at t_0, 3-d vectors,
    frame_0: the frame quaternion at t_0, quaternionic_array object,
    t_0: the corresponding time of the above given initial values, float number,
    t_PNStart: the start time of PN relative to t_0: t_PNStart=t_real_start-t_0, float number. If false, default is t_0-t_real_start=3(t_merger-t_0),
    t_PNEnd: the end time of PN relative to t_0: t_PNEnd=t_real_end-t_0, float number. If false, default is merger time,
    datatype: "h" for strain and "Psi_M" for Moreschi supermomentum,
    return_chi: whether to return chi as quaternion array of time, bool number,
    PNEvolutionOrder: float number in [0,0.5,1,1.5,2,2.5,3,3.5,4], default is 3.5,
    PNWaveformModeOrder: float number in [0,0.5,1,1.5,2,2.5,3,3.5,4], default is 3.5,
    TaylorTn: now only TaylorT1 is working, so its int number in [1], default is 1,
    StepsPerOrbit: float number,
    ForwardInTime: whether to evlove PN forward in time, bool number, default if True,
    tol: tolerance of the integrator, float number,
    MinStep: minimal time interval for the PN waveform, float number.
    """

    if not PNEvolutionOrder in [0,0.5,1,1.5,2,2.5,3,3.5,4]:
        message=("PNEvolutionOrder must be a float number in [0,0.5,1,1.5,2,2.5,3,3.5,4].")
        raise ValueError(message)
    if not PNWaveformModeOrder in [0,0.5,1,1.5,2,2.5,3,3.5,4]:
        message=("PNWaveformModeOrder must be a float number in [0,0.5,1,1.5,2,2.5,3,3.5,4].")
        raise ValueError(message)
    if not TaylorTn in [1]:
        message=("TaylorTn must be an int number in [1].")
        raise ValueError(message)          

    wHat=quaternionic.one
    xHat=quaternionic.x
    yHat=quaternionic.y
    zHat=quaternionic.z
    m1=q/(1+q)*M
    m2=1/(1+q)*M
    v_0=omega_0**(1/3)
    chi1Mag=quaternionic.array([0,chi1_0[0],chi1_0[1],chi1_0[2]]).abs
    chi2Mag=quaternionic.array([0,chi2_0[0],chi2_0[1],chi2_0[2]]).abs

    # Quaternions that rotate z-axis to spin vectors
    S_chi1_0=0.0*quaternionic.one 
    S_chi2_0=0.0*quaternionic.one
    if chi1Mag>1e-12:
        S_chi1_0=np.sqrt(chi1Mag)*np.sqrt(
            -quaternionic.array([0,chi1_0[0],chi1_0[1],chi1_0[2]]).normalized*zHat).normalized
    if chi2Mag>1e-12:
        S_chi2_0=np.sqrt(chi2Mag)*np.sqrt(
            -quaternionic.array([0,chi2_0[0],chi2_0[1],chi2_0[2]]).normalized*zHat).normalized
  
    PN=PNEvolution1.PNEv.Evolution(wHat, xHat, yHat, zHat, m1, m2, v_0,S_chi1_0, S_chi2_0, quaternion.as_float_array(frame_0), t_PNStart, t_PNEnd,
        PNEvolutionOrder, TaylorTn, StepsPerOrbit, ForwardInTime, tol, MinStep)# Evolve PN parameters, PN.t is PN time, PN.y=[v, chi1_x, chi1_y
                                                        # chi2_x, chi2_y, frame_w, frame_x, frame_y, frame_z]
    W_PN_corot=scri.WaveformModes()
    W_PN_corot.t=PN.t+t_0
    W_PN_corot.frame=quaternion.from_float_array(np.column_stack((PN.y[5],PN.y[6],PN.y[7],PN.y[8])))
    for i in range(len(W_PN_corot.frame)):
        W_PN_corot.frame[i]=W_PN_corot.frame[i].normalized()
    if datatype=="h":
        W_PN_corot.data, W_PN_corot.ells = PNWaveformModes.Modes(wHat, xHat, yHat, zHat, m1, m2, v_0,S_chi1_0, S_chi2_0, quaternion.as_float_array(frame_0), PN.y, PNWaveformModeOrder)
        W_PN_corot.dataType=scri.h
    elif datatype=="Psi_M":
        W_PN_corot.data, W_PN_corot.ells = PNPsiMModes.Modes(wHat, xHat, yHat, zHat, m1, m2, v_0,S_chi1_0, S_chi2_0, quaternion.as_float_array(frame_0), PN.y, PNWaveformModeOrder)
        W_PN_corot.dataType=scri.psi2
        W_PN_corot.data[:,0]=W_PN_corot.data[:,0]-1.0

    if return_chi:
        R_S1=np.exp(PN.y[1]*xHat + PN.y[2]*yHat)
        R_S2=np.exp(PN.y[3]*xHat + PN.y[4]*yHat)
        chiVec1=quaternion.from_float_array(S_chi1_0*R_S1*zHat*R_S1.conjugate()*S_chi1_0.conjugate())
        chiVec2=quaternion.from_float_array(S_chi2_0*R_S2*zHat*R_S2.conjugate()*S_chi2_0.conjugate())
        return W_PN_corot, chiVec1, chiVec2
    else:
        return W_PN_corot
