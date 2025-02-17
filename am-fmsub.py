import numpy as np
import matplotlib.pyplot as plt

fs = 44100
duration = 1.0
t = np.linspace(0, duration, int(fs*duration), endpoint=False)

# AM parameters
f_am = 2.0
m_a = 0.5
# Envelope is defined as 1 + m_a * sin(2 * pi * f_am * t)
envelope = 1 + m_a * np.sin(2 * np.pi * f_am * t)

# FM parameters
f_c = 1000
f_fm = 5
beta = 5

# Instantaneous phase for FM is 
# phi(t) = 2 * pi * f_c * t + beta * sin(2 * pi * f_fm * t)
phase = 2 * np.pi * f_c * t + beta * np.sin(2 * np.pi * f_fm * t)
fm_subcarrier = np.cos(phase)

# The resulting AM signal with FM subcarrier:
am_fm_signal = envelope * fm_subcarrier

# FFT of the signals
fft_signal = np.fft.fft(am_fm_signal)
fft_freq = np.fft.fftfreq(len(am_fm_signal), d=1/fs)
idx = np.where(fft_freq > 0)

# Plotting the signals

plt.figure(figsize=(10, 6))
segment = int(0.1 * fs)
time_segment = t[:segment]

plt.subplot(4, 1, 1)
plt.plot(time_segment, envelope[:segment])
plt.title('AM envelope')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')

plt.subplot(4, 1, 2)
plt.plot(time_segment, fm_subcarrier[:segment])
plt.title('FM subcarrier')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')

plt.subplot(4, 1, 3)
plt.plot(time_segment, am_fm_signal[:segment])
plt.title('AM signal with FM subcarrier')  
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')

plt.subplot(4, 1, 4)
plt.plot(fft_freq[idx], np.abs(fft_signal[idx]) / len(am_fm_signal))
plt.title("Spectrum of AM signal with FM subcarrier")
plt.xlabel('Frequency (Hz)')
plt.ylabel('Magnitude')
plt.grid(True)

plt.tight_layout()
plt.show()