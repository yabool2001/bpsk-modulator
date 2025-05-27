import adi
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import lfilter
import sys

# Import lokalnego modułu RRC
sys.path.append ( "modules" )
from rrc import rrc_filter

# App settings
#verbose = True
verbose = False

# Parametry systemu
F_C = 2_900_000_000
F_S = 521_100
BW  = 20_000_000
NUM_SAMPLES = 4096
NUM_POINTS = 16384
# Parametry filtru RRC
RRC_BETA = 0.35
RRC_SPS = 8
RRC_SPAN = 11

# Inicjalizacja Pluto SDR
sdr = adi.Pluto ( uri = "usb:" )
sdr.rx_lo = F_C
sdr.sample_rate = int ( F_S )
sdr.rx_rf_bandwidth = BW
sdr.rx_buffer_size = NUM_SAMPLES
sdr.gain_control_mode_chan0 = "manual"
sdr.rx_hardwaregain_chan0 = -3.0
print ( f"Typ danych RX: {sdr._rx_data_type}" )
print ( f"{sdr.rx_hardwaregain_chan0=}")
print ( f"{sdr=}" )

# Bufor konstelacji (cykliczny)
iq_buffer = np.zeros ( NUM_POINTS , dtype = np.complex64 )
write_index = 0

# Inicjalizacja filtru RRC
rrc_taps = rrc_filter ( RRC_BETA , RRC_SPS , RRC_SPAN )

# Wykresy – interaktywny tryb
plt.ion ()
fig , ( ax_time , ax_const ) = plt.subplots ( 2 , 1 , figsize = ( 10 , 6 ) )

line_i , = ax_time.plot ( np.zeros ( NUM_SAMPLES ) , label = "I" )
line_q , = ax_time.plot ( np.zeros ( NUM_SAMPLES ) , label = "Q" )
ax_time.set_title ( "Sygnał w dziedzinie czasu" )
ax_time.set_xlabel ( "Próbka" )
ax_time.set_ylabel ( "Amplituda" )
ax_time.set_ylim ( -1.0 , 1.0 )
ax_time.grid ( True )
ax_time.legend ()

sc_const = ax_const.scatter (
    np.real ( iq_buffer ) ,
    np.imag ( iq_buffer ) ,
    s = 6 ,
    color = "blue"
)
ax_const.set_title ( "Diagram konstelacyjny (ostatnie punkty)" )
ax_const.set_xlabel ( "I" )
ax_const.set_ylabel ( "Q" )
ax_const.grid ( True )
ax_const.set_xlim ( -1.2 , 1.2 )
ax_const.set_ylim ( -1.2 , 1.2 )
ax_const.set_aspect ( "equal" )

plt.tight_layout ()

try:
    while True:
        new_samples = sdr.rx()
        #new_samples = np.array ( sdr.rx () )
        new_samples = lfilter ( rrc_taps , 1.0 , new_samples )
        
        if verbose :
            print ( f"Typ danych: {type ( new_samples )}, dtype: {new_samples.dtype}" )
            print ( f"{new_samples=}" )
            print ( f"Max amp: {np.max ( np.abs ( new_samples ) ):.3f}" )

        n = len ( new_samples )
        max_amp = np.max ( np.abs ( new_samples ) )

        if max_amp > 0.01:
            print ( f"Amp: {max_amp:.3f} , dodano {n} próbek" )

            if write_index + n <= NUM_POINTS:
                iq_buffer[write_index : write_index + n] = new_samples
            else:
                first_chunk = NUM_POINTS - write_index
                iq_buffer[write_index : ] = new_samples[ : first_chunk]
                iq_buffer[ : n - first_chunk] = new_samples[first_chunk : ]
            write_index = ( write_index + n ) % NUM_POINTS

            line_i.set_ydata ( np.real ( new_samples ) )
            line_q.set_ydata ( np.imag ( new_samples ) )
            ax_time.set_xlim ( 0 , NUM_SAMPLES )

        iq_plot = np.roll ( iq_buffer , -write_index )
        sc_const.set_offsets (
            np.column_stack (
                ( np.real ( iq_plot ) , np.imag ( iq_plot ) )
            )
        )

        fig.canvas.draw ()
        fig.canvas.flush_events ()

except KeyboardInterrupt:
    print ( "\nZatrzymano monitorowanie sygnału." )
    plt.ioff ()
    plt.show ()
