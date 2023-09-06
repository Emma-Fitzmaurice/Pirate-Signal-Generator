from PIL import Image, ImageDraw, ImageFont
from ST7789 import ST7789
import RPi.GPIO as GPIO
import signal

SPI_SPEED_MHZ = 80
st7789 = ST7789(
    rotation=90,  # Needed to display the right way up on Pirate Audio
    port=0,       # SPI port
    cs=1,         # SPI port Chip-select channel
    dc=9,         # BCM pin used for data/command
    backlight=13,
    spi_speed_hz=SPI_SPEED_MHZ * 1000 * 1000
)


image = Image.new("RGB", (240, 240), (0, 0, 0))
draw = ImageDraw.Draw(image)
font = ImageFont.truetype("AtkinsonHyperlegible-Regular.ttf", 19)
small_font = ImageFont.truetype("AtkinsonHyperlegible-Regular.ttf", 12)
colour_palette = ["#65A1F6","#4DA167","#52489C","#EF6F6C"]
sine_img = Image.open("Sine_wave.png")
white_img = Image.open("White_Noise.png")
pink_img = Image.open("Pink_Noise.png")
waves = ["Sine","Triangle","Square","Sawtooth","Inv Saw","White","Pink","Octaves","1/2 Oct","1/3 Oct","Semitone","Whole Tone"]
wave_freq = 1000
oct_freq = 440
level = -6
wave_index = 0
resolution = 0 # [Coarse, Fine, Finest]
active_param = 0 # [Wave, Frequency, Level]



###########################
# Parameter Control
###########################

def cycle_wave(inc = True):
    global wave_index
    wave_index += 1 if inc else -1
    wave_index %= len(waves)
    render_display()

def cycle_freq(inc = True):
    global wave_freq, oct_freq, active_freq
    if wave_index < 5:
        if resolution == 0:
            wave_freq += 100 if inc else -100
        elif resolution == 1:
            wave_freq += 10 if inc else -10
        elif resolution == 2:
            wave_freq += 1 if inc else -1
        wave_freq %=20000    
    elif wave_index > 6:
        if resolution == 0:
            oct_freq += 100 if inc else -100
        elif resolution == 1:
            oct_freq += 10 if inc else -10
        elif resolution == 2:
            oct_freq += 1 if inc else -1
        oct_freq %=20000
    render_display()

def cycle_level(inc = True):
    global level
    if resolution ==  0:
        level += 6 if inc else -6
    elif resolution ==  1:
        level += 1 if inc else -1
    elif resolution ==  2:
        level += 0.1 if inc else -0.1
    level = min(0,level)
    render_display()


###########################
# GUI
###########################
def draw_octave_lines(num_lines):
    draw.line([15,115,185,115],width=2)
    for i in range(num_lines):
        draw.line([((i+1)*170/(num_lines+1)+15),115,(((i+1)*170/(num_lines+1))+15),25],width=2)



def render_display():

    draw.rectangle([0,0,200,160],fill=colour_palette[0])
    draw.rectangle([0,160,200,200],fill=colour_palette[1])
    draw.rectangle([0,200,200,240],fill=colour_palette[2])
    # Parameter seperators
    draw.line([0,160,200,160])
    draw.line([0,200,200,200])

    draw.text((15, 127),"Wave : %s" % waves[wave_index],(255,255,255),font)
    draw.text((15, 207),"Level : %s dBV" % level,(255,255,255),font)
    if wave_index < 5:
        draw.text((15, 167),"Frequency : %shz" % wave_freq,(255,255,255),font)
    elif wave_index > 6:
        draw.text((15, 167),"Frequency : %shz" % oct_freq,(255,255,255),font)

    # B button Arrow
    draw.line([6,140,6,220],width=1)
    draw.line([4,218,6,220,8,218],width=1)

    # A button, Control Resolution
    draw.rectangle([0,0,60,16],fill=colour_palette[3])
    draw.rectangle([0,0,8,75],fill=colour_palette[3])
    draw.line([0,75,8,75,8,16,60,16,60,0],width=1)
    
    if resolution ==  0:
        draw.text((15,0), "Coarse", font=small_font)
    elif resolution ==  1:
        draw.text((15,0), "Fine", font=small_font)
    elif resolution ==  2:
        draw.text((15,0), "X-Fine", font=small_font)



    if active_param ==0:
        draw.rectangle([200,0,240,240],fill=colour_palette[0])
        draw.line([200,160,200,240])
    elif active_param == 1:
        draw.rectangle([200,0,240,240],fill=colour_palette[1])
        draw.line([200,0,200,160])
        draw.line([200,200,200,240])
    elif active_param == 2:
        draw.rectangle([200,0,240,240],fill=colour_palette[2])
        draw.line([200,0,200,200])
    
    # draw +
    draw.line([215,70,225,70],width=3)
    draw.line([220,65,220,75],width=3)
    # draw -
    draw.line([215,190,225,190],width=3)



    if wave_index == 0: # Sine
        image.paste(sine_img,[15,25],mask=sine_img)
    elif wave_index == 1: # Triangle
        draw.line([15,70,57.5,25,100,70,142.5,115,185,70],width=2)
    elif wave_index == 2: # Square
        draw.line([15,70,15,25,100,25,100,115,185,115,185,70],width=2)
    elif wave_index == 3: # Saw
        draw.line([15,115,185,25,185,115,185,25],width=2)
    elif wave_index == 4: # Inv Saw
        draw.line([15,115,15,25,185,115,185,25],width=2)
    elif wave_index == 5: # White
        image.paste(white_img,[15,25])
    elif wave_index == 6: # Pink
        image.paste(pink_img,[15,25])
    elif wave_index == 7: # Octaves
        draw_octave_lines(1)
    elif wave_index == 8: # 1/2 Oct
        draw_octave_lines(2)
    elif wave_index == 9: # 1/3 Oct
        draw_octave_lines(3)
    elif wave_index == 10: # Whole Tone
        draw_octave_lines(6)
    elif wave_index == 11: # Semitone
        draw_octave_lines(12)
    
    st7789.display(image)

###########################
# Audio (SuperCollider control)
###########################



###############

BUTTONS = [5, 6, 16, 24]

# These correspond to buttons A, B, X and Y respectively
LABELS = ['A', 'B', 'X', 'Y']

# Set up RPi.GPIO with the "BCM" numbering scheme
GPIO.setmode(GPIO.BCM)

# Buttons connect to ground when pressed, so we should set them up
# with a "PULL UP", which weakly pulls the input signal to 3.3V.
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def handle_button(pin):
    global resolution
    global active_param
    
    if pin == 5: # A
        resolution +=1
        resolution %=3
        render_display()
        print("inc resolution")
    elif pin ==  6: # B
        active_param +=1
        active_param %=3
        render_display()
        print("inc param " +str(active_param))
    elif pin ==  16: # X
        if active_param == 0:
            cycle_wave()
            render_display()
            print("inc wave")
        elif active_param ==  1:
            cycle_freq()
            render_display()
            print("inc freq")
        elif active_param ==  2:
            cycle_level()
            render_display()
            print("inc level")
    elif pin ==  24: # Y
        if active_param == 0:
            cycle_wave(False)
            render_display()
            print("dec wave")
        elif active_param ==  1:
            cycle_freq(False)
            render_display()
            print("dec freq")
        elif active_param ==  2:
            cycle_level(False)
            render_display()
            print("dec level")

for pin in BUTTONS:
    GPIO.add_event_detect(pin, GPIO.FALLING, handle_button, bouncetime=100)
    
render_display()
signal.pause()