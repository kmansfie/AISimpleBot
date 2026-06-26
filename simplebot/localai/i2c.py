def de_energize():
    try:
        pca.channels[LEFT].duty_cycle = 0
        pca.channels[RIGHT].duty_cycle = 0
    except OSError:
        print("[!] I2C Write Failed during de-energize")

def move(l_pulse, r_pulse, duration):
    try:
        pca.channels[LEFT].duty_cycle = int((l_pulse / 20.0) * 65535)
        pca.channels[RIGHT].duty_cycle = int((r_pulse / 20.0) * 65535)
        time.sleep(duration)
        de_energize()
    except OSError:
        print("[!] I2C Write Failed during move")

