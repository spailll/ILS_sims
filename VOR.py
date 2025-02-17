import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import hilbert

# Parameters
fs = 1000       # Sampling rate
duration = 1.0  # Duration in seconds
t = np.linspace(0, duration, int(fs*duration), endpoint=False)

f_mod = 30      # Modulation frequency (Hz) for VOR signals

# True azimuth (in degrees) for the simulation
# In a VOR system, the phase difference between the reference and variable signals correspond to the azimuth
true_azimuth_deg = 45
true_azimuth_rad = np.deg2rad(true_azimuth_deg)

# GENERATE THE SIGNALS

# Reference signal (omnidirectional) - a pure sine wave at f_mod Hz 
ref_signal = np.sin(2 * np.pi * f_mod * t)

# Variable signal (rotating antenna signal) - same freqnecy, but phase-shifted by the true azimuth
var_signal = np.sin(2 * np.pi * f_mod * t + true_azimuth_rad)


# EXTRACT INSTANTANEOUS PHASE USING HILBERT TRANSFORM

ref_analytic = hilbert(ref_signal)
var_analytic = hilbert(var_signal)

# Unwarp the phase (to remove discontinuities)
ref_phase = np.unwrap(np.angle(ref_analytic))
var_phase = np.unwrap(np.angle(var_analytic))

# Compute the phase difference
phase_diff = var_phase - ref_phase

# For a stable measurement, take the mean phase difference over the duration of the signal
mean_phase_diff = np.mean(phase_diff)

# Convert the mean phase difference to digrees and normalize (wrap to 0-360 degrees)
computed_azimuth_deg = np.rad2deg(mean_phase_diff) % 360

print(f"True azimuth: {true_azimuth_deg} degrees")
print(f"Computed azimuth: {computed_azimuth_deg} degrees")

# PLOTTING
plt.figure(figsize=(12, 8))
segment = int(0.1 * fs)
t_segment = t[:segment]

plt.subplot(3, 1, 1)
plt.plot(t_segment, ref_signal[:segment], label='Reference signal')
plt.plot(t_segment, var_signal[:segment], label='Variable signal')
plt.title('VOR Signals (First 0.1 seconds)')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.legend()

plt.subplot(3, 1, 2)
plt.plot(t_segment, ref_phase[:segment], label='Reference signal')
plt.plot(t_segment, var_phase[:segment], label='Variable signal')
plt.title('Instantaneous Phase of VOR Signals')
plt.xlabel('Time (s)')
plt.ylabel('Phase (radians)')
plt.legend()

plt.subplot(3, 1, 3)
plt.plot(t_segment, phase_diff[:segment], color='magenta')
plt.title('Phase Difference between Reference and Variable Signals')
plt.xlabel('Time (s)')
plt.ylabel('Phase Difference (radians)')

plt.tight_layout()
plt.show()


