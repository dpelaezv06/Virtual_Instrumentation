import numpy as np
import matplotlib.pyplot as plt

# Signals parameters
# Carrier signal - high frequency
Carrier_amplitude = 0.5 # Amplitude of the carrier signal
Carrier_frequency = 200 # Frequency of the carrier signal

# Modulator signal (message) - low frequency 
Modulator_amplitude = 1 # Amplitude of the modulator signal
Modulator_frequency = 20 # Frequency of the modulator signal

# Modulation index A_m/A_c
modulation_index = 0.5 

# time vector
time = np.linspace(0, 1, 1000) # 1 second duration, 1000 samples

# Definition of signals
Carrier_signal = Carrier_amplitude * np.cos(2*np.pi*Carrier_frequency*time)
Modulator_signal = Modulator_amplitude * np.cos(2*np.pi*Modulator_frequency*time)

Modulated_signal = (Carrier_amplitude + Modulator_signal) * np.cos(2*np.pi*Carrier_frequency*time)

plt.subplot(3,1,1)
plt.title('Amplitude Modulation')
plt.plot(Modulator_signal,'g')
plt.ylabel('Amplitude')
plt.xlabel('Message signal')

plt.subplot(3,1,2)
plt.plot(Carrier_signal, 'r')
plt.ylabel('Amplitude')
plt.xlabel('Carrier signal')

plt.subplot(3,1,3)
plt.plot(Modulated_signal, color="purple")
plt.ylabel('Amplitude')
plt.xlabel('AM signal')

plt.subplots_adjust(hspace=1)
plt.rc('font', size=15)
fig = plt.gcf()
fig.set_size_inches(16, 9)

plt.show()

print("Modulation index (A_m/A_c):", modulation_index)
