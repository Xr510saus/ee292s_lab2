import RPi.GPIO as GPIO
import time
import ADS1256
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Ellipse

# contains func for generating PRBS sequence from HW
from prbs import *

# for debugging
PLOTTING = True

# GPIO pins for each drive line
DRIVE1 = 7
DRIVE2 = 12
DRIVE3 = 16
DRIVE4 = 20
DRIVE5 = 21

DRIVE_LINES = [DRIVE1, DRIVE2, DRIVE3, DRIVE4, DRIVE5]

# Drive GPIO lines with evenly spaced phase-shifted PRBS sequences
# def drive_prbs(prbs_seq):
#     spacing = len(prbs_seq) // 5
#     seqLen = len(prbs_seq)

#     for x in range(len(prbs_seq)):
#         for line in range(len(DRIVE_LINES)):
#             prbs_seq[(x + line*spacing) % seqLen]
#             if bit==1:
#                 GPIO.output(drive_line, True)
#             else:
#                 GPIO.output(drive_line, False)

# init ADC
ADC = ADS1256.ADS1256()
ADC.ADS1256_init()

# init GPIO output pins
GPIO.setmode(GPIO.BCM)
for drive_line in DRIVE_LINES:
    GPIO.setup(drive_line, GPIO.OUT)


bits = 5 # PRBS length
seqLen = (2**bits - 1)
spacing = 2**bits // 5 # evenly divide spacing

adcvals = np.zeros((7, seqLen)) # init ADC channels

# init baseline calibration ADC array
notouch_adcvals = np.zeros((7, seqLen))
notouch_xcorr = np.zeros((7, seqLen))

x = np.arange(0, seqLen)
# print(x)
temp = np.zeros(seqLen)
# print(temp)
# y1 = np.zeros(20)

# PRBS CROSS-CORR PLOT
fig = plt.figure(figsize=(10,6))
axes = fig.subplots(nrows=1)
axes.set_ylim(0, seqLen)
ticks = np.arange(0, seqLen+1, seqLen//5)
axes.set_yticks(ticks)
axes.set_yticklabels(ticks)

# HEAT MAP PLOT
heatfig, heatax = plt.subplots()
heat_data = np.random.rand(7,5)
heatmap = heatax.imshow(heat_data, cmap='viridis', vmin=0, vmax=30)
colorbar = plt.colorbar(heatmap)

# CENTROID/ELLIPSE PLOT
centroidfig, centroidax = plt.subplots()
centroidax.set_ylim(0, 6)
centroidax.set_xlim(0, 4)
centroidax.set_aspect('equal') # fixed aspect ratio
centroidax.invert_yaxis() # invert axis to match heat map
# Initialize data
centroid_x = 0.0
std_dev_x = 0.0
centroid_y = 0.0
std_dev_y = 0.0
# Plot initial centroid and ellipse
centroid = centroidax.scatter(centroid_x, centroid_y, color='red', marker='.', s=100, label='Centroid')

ellipse = Ellipse(xy=(centroid_x, centroid_y), width=2 * std_dev_x, height=2 * std_dev_y,
                  edgecolor='blue', fc='None', lw=2)
centroidax.add_patch(ellipse)


JITTER_TEST = True # for measuring noise of still contact
jitter_start_time = time.time()
x_jitter = []
y_jitter = []
### Animated function for centroid live-plotting
def update_centroid(frame):
    # Generate meshgrid for x and y coordinates
    # print(heat_data.shape)
    dense_x, dense_y = np.meshgrid(np.arange(heat_data.shape[1]), np.arange(heat_data.shape[0]))

    # Calculate the centroid coordinates
    centroid_x = np.sum(dense_x * heat_data) / np.sum(heat_data)
    centroid_y = np.sum(dense_y * heat_data) / np.sum(heat_data)

    global JITTER_TEST
    if JITTER_TEST == False:
        global jitter_start_time
        global x_jitter
        global y_jitter
        if time.time() - jitter_start_time > 5: # wait 5 seconds at start
            if len(x_jitter) < 1000: # take 1000 samples
                print(f'x_len={len(x_jitter)}')
                x_jitter.append(centroid_x)
                y_jitter.append(centroid_y)
            else: # compute RMS noise after hitting 1000 samples
                x_jitter = np.array(x_jitter)
                y_jitter = np.array(y_jitter)
                centroid_coordinates = np.column_stack((x_jitter, y_jitter))
                motion = np.diff(centroid_coordinates, axis=0)
                squared_motion = np.sum(np.square(motion), axis=1)
                rms_noise = np.sqrt(np.mean(squared_motion))
                print(f'rms_noise={rms_noise}')



    # Calculate the standard deviations
    std_dev_x = np.sqrt(np.sum((dense_x - centroid_x)**2 * heat_data) / np.sum(heat_data))
    std_dev_y = np.sqrt(np.sum((dense_y - centroid_y)**2 * heat_data) / np.sum(heat_data))

    # Update centroid plot
    centroid.set_offsets(np.array([centroid_x, centroid_y]))

    # Update ellipse plot
    ellipse.set_center((centroid_x, centroid_y))
    ellipse.set_width(2 * std_dev_x)
    ellipse.set_height(2 * std_dev_y)

    return centroid, ellipse


# NOTE: indices:
# drive0: 7
# drive1: 13
# drive2: 19
# drive3: 25
# drive4: 0
old_frame = 0.0 # for framerate calculation

### Animated function for heat map live-plotting
def update_heat(frame):
    global heat_data
    # global old_frame
    threshold = 2
    for sense in range(7):
        for i,x in enumerate([7, 13, 19, 25, 0], start=0):
            heat_data[sense, i] = lines[sense].get_ydata()[x] if lines[sense].get_ydata()[x] > threshold else 0
    heatmap.set_array(heat_data)
    # print(f'lines: {lines[1].data}')
    # heatax.autoscale()
    return heatmap,

# print(axes)

styles = ['r-', 'g-', 'y-', 'm-', 'k-', 'c-', 'b-']
def plot(ax, style):
    # print(x)
    return ax.plot(x, temp, style, animated=True)[0]
# print(x)
lines = [plot(axes, style) for style in styles]#ax, style) for ax, style in zip(axes, styles)]

### Baseline calibration during no-touch on program start
def notouch_calibrate():
    for sense in range(7):
        ADC.ADS1256_SetChannal(sense)
        prbs_seq = PRBS(bits, 0)

        prbs_seq = [-1 if z==0 else 1 for z in prbs_seq]

        for x in range(len(prbs_seq)):
            for line in range(len(DRIVE_LINES)):
                bit = prbs_seq[(x + line*spacing) % seqLen]
                if bit==1:
                    GPIO.output(DRIVE_LINES[line], True)
                else:
                    GPIO.output(DRIVE_LINES[line], False)
            # time.sleep(0.001)
            # ADC_Value = ADC.ADS1256_GetAll()
            ADC_Value = ADC.ADS1256_GetChannalValue(sense)
            notouch_adcvals[sense,x] = ADC_Value*5.0/0x7fffff
        notouch_xcorr[sense] = xcorr(notouch_adcvals[sense], prbs_seq)

    print("No touch calibration complete!")

### PRBS live-plotting function
def animate(i):
    global old_frame
    y = [np.random.normal() for j in range(seqLen)]
    # y1 = [np.random.normal() for j in range(20)]

    # line = axes.plot(x, y, styles, animated=True)[0]

    # line.set_ydata(y)

    for sense in range(7):
        ADC.ADS1256_SetChannal(sense)
        prbs_seq = PRBS(bits, 0)

        prbs_seq = [-1 if z==0 else 1 for z in prbs_seq]

        for x in range(len(prbs_seq)):
            for line in range(len(DRIVE_LINES)):
                bit = prbs_seq[(x + line*spacing) % seqLen]
                if bit==1:
                    GPIO.output(DRIVE_LINES[line], True)
                else:
                    GPIO.output(DRIVE_LINES[line], False)
            # time.sleep(0.001)
            # ADC_Value = ADC.ADS1256_GetAll()
            ADC_Value = ADC.ADS1256_GetChannalValue(sense)
            adcvals[sense,x] = ADC_Value*5.0/0x7fffff

            # adcvals[:,x] = ADC.ADS1256_GetAll()

    # for sdata in adcvals:
    #     pass

    #print(adcvals)

    for j, line in enumerate(lines, start=0):
        #print(j)
        line.set_ydata(xcorr(adcvals[j], prbs_seq) - notouch_xcorr[j]) #adcvals[j])
        if j == 0:
            temp = np.argsort(line.get_ydata())[-5:]
            # print(temp, line.get_ydata()[temp])

        # print(len(xcorr(adcvals[j], prbs_seq)))
    new_frame = time.time()
    framerate = 1.0 / (new_frame - old_frame)
    old_frame = new_frame
    # print(f'fps: {framerate}')
    return lines

notouch_calibrate() # grab baseline at start for subtracting offset

# Event loops for real-time plots
ani = animation.FuncAnimation(fig, animate, interval=0, blit=True, repeat=True)             # PRBS cross-corr plots
heatani = animation.FuncAnimation(heatfig, update_heat,interval=0, blit=True)               # heat map
centroidani = animation.FuncAnimation(centroidfig, update_centroid,interval=0, blit=True)   # centroid + ellipse map

plt.show()

GPIO.cleanup()