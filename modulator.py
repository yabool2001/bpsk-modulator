import numpy as np
import zlib
import adi
import time

# Parametry transmisji
F_C = 820_000_000            # częstotliwość nośna [Hz]
F_S = 521_100                 # szybkość próbkowania [Hz]
SPS = 8                      # samples per symbol
SILENCE_MS = 1000            # cisza po pakiecie [ms]
MAX_PAYLOAD_LEN = 255        # maksymalna długość payloadu

# Preambuła
PREAMBLE = bytes ( [0xAA] * 4 + [0x55] * 4 )
silence_samples = int ( F_S * SILENCE_MS / 1000 )
silence = np.zeros ( silence_samples, dtype = np.complex64 )

# Wczytaj dane z pliku
with open ( "input.txt", "rb" ) as f:
    full_data = f.read ()

# Lista sygnałów do połączenia
tx_signal_parts = []

for i in range ( 0, len ( full_data ), MAX_PAYLOAD_LEN ):
    
    payload = full_data[i : i + MAX_PAYLOAD_LEN]
    length_byte = len ( payload ).to_bytes ( 1, "big" )

    # Timestamp (ms od epoch)
    timestamp_ms = int ( time.time () * 1000 ) & 0xFFFFFFFF
    timestamp_bytes = timestamp_ms.to_bytes ( 4, "big" )

    # CRC dla: LEN + TIMESTAMP + PAYLOAD
    crc_input = length_byte + timestamp_bytes + payload
    crc = zlib.crc32 ( crc_input )
    crc_bytes = crc.to_bytes ( 4, "big" )

    # Zbuduj pakiet: PREAMBLE + HEADER + PAYLOAD + CRC
    packet = PREAMBLE + crc_input + crc_bytes

    # Konwersja na bity i symbole BPSK
    packet_bits = np.unpackbits ( np.frombuffer ( packet, dtype = np.uint8 ) )
    symbols = 2 * packet_bits - 1
    tx_symbols = np.repeat ( symbols, SPS ).astype ( np.complex64 )
    tx_symbols *= 0.5

    # Dodaj sygnał i ciszę
    tx_signal_parts.append ( tx_symbols )
    tx_signal_parts.append ( silence )

# Łączna sekwencja
tx_signal = np.concatenate ( tx_signal_parts )

# Inicjalizacja Pluto SDR
sdr = adi.Pluto ( uri = "usb:" )

sdr.sample_rate = F_S
sdr.tx_rf_bandwidth = int ( F_S )
sdr.tx_lo = F_C
sdr.tx_cyclic_buffer = False

# Nadawanie
sdr.tx ( tx_signal )

print ( f"Wysłano {len ( tx_signal_parts ) // 2} pakietów z F_C = {F_C / 1e6:.1f} MHz, F_S = {F_S / 1e6:.1f} MS/s, SPS = {SPS}." )
