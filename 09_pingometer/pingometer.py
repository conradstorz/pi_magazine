import subprocess
import time
import sys

try:
    import RPi.GPIO as GPIO
    RPI_FOUND = True
    from squid import *
except ImportError:
    print ('CODE ERROR:')
    print ('Raspberry Pi compatible GPIO required for this code.')
    RPI_FOUND = False
    GREEN = 'Green'
    RED = 'Red'
    ORANGE = 'Orange'
    BLUE = 'Blue'



HOSTS_LIST = ["www.google.com", 'www.facebook.com', 'www.twitter.com', 'www.yahoo.com', 
                'www.linkedin.com', 'www.stackoverflow.com', 'www.ebay.com', 'www.live.com',
                'www.wikipedia.org', 'www.apple.com', 'www.reddit.com', 'www.wordpress.com']
# HOSTNAME = "google.com"
PING_PERIOD = 3.0 # seconds
GOOD_PING = 0.1   # seconds
OK_PING = 0.3     # seconds

SERVO_PIN = 25 # control pin of servo
MIN_ANGLE = 30
MAX_ANGLE = 150

if RPI_FOUND:
    # Configure the GPIO pin
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    pwm = GPIO.PWM(SERVO_PIN, 100) # start PWM at 100 Hz
    pwm.start(0)
    # initialize squid
    SQUID_GPIO_RED = 18
    SQUID_GPIO_BLUE = 23
    SQUID_GPIO_GREEN = 24
    squid = Squid(SQUID_GPIO_RED, SQUID_GPIO_GREEN, SQUID_GPIO_BLUE)

test_outputs = True

def map_ping_to_angle(ping_time):
    # ping timeout of 1000 ms sets maximum
    # ping min of 0
    # Fast ping needle over to the right
    angle = ping_time * (MAX_ANGLE - MIN_ANGLE) + MIN_ANGLE
    if angle > MAX_ANGLE :
        angle = MAX_ANGLE
    if angle < MIN_ANGLE :
        angle = MIN_ANGLE
    return angle

# Set the servo to the angle specified
def set_angle(angle):
    duty = float(angle) / 10.0 + 2.5
    if RPI_FOUND:
        pwm.ChangeDutyCycle(duty)
    else:
        print(f'set pwm duty cycle...{duty}')
    time.sleep(0.2); # give the arm time to move
    if RPI_FOUND:
        pwm.ChangeDutyCycle(0) # stop servo jitter

def clean_output(itms):
    times = []
    for i in itms:
        quarks = i.split('=')
        if quarks[0] == 'time':
            times.append(quarks[1])
    return times


def ping(hostname):
    try:
        output = subprocess.run("ping " + hostname, capture_output=True)
        items = str(output.stdout).split()
        print(f'CMD output: {items}')
        times = clean_output(items)
        return float(int(times[0][:-2]) / 1000.0) #TODO avg times together not just first one
    except error as e:
        print(f'Ping CMD failed with error {e}')
        return 1


def set_squid(color):
    if RPI_FOUND:
        squid.set_color(color)
    else:
        print(f'LED color: {color}')


def display_status(ping):
    if ping == -1 :
        set_squid(BLUE)
    elif ping < GOOD_PING:
        set_squid(GREEN)
    elif ping < OK_PING:
        set_squid(ORANGE)
    else:
        set_squid(RED)

try:
    if test_outputs:
        for x in range(10):
            test_value = float(x) / 10
            print ('Test value: ', test_value)
            set_angle(map_ping_to_angle(test_value))
            display_status(test_value)
            
    while True:
        total_ping = 0
        for host in HOSTS_LIST:
            print(f'Pinging: {host}')
            result = ping(host)
            print(f'Ping time: {result}')
            total_ping += result
            time.sleep(.5)
        # p = input("ping=")  # Use for testing
        print(f'Total Ping: {total_ping}')
        avg_ping = total_ping / len(HOSTS_LIST)
        print(f'Average Ping: {avg_ping}')
        set_angle(map_ping_to_angle(avg_ping))
        display_status(avg_ping)
        time.sleep(PING_PERIOD)
finally:
    if RPI_FOUND:
        GPIO.cleanup()
