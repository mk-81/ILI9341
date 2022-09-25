# ILI9341
Modified version of Adafruids archvived ILI9341 (from library with https://github.com/adafruit/Adafruit_Python_ILI9341) multiple extensions/adjustments ported **only** for Raspberry Pi. The library has some performance improvements compared to the original one.

## Installation
* Optional: Activate your Python virtual environment you want to use.
* Clone the reporitory (e.g. to your project path) and enter the newly created directory.
* Run `pip install .`

*The sources will be cytonized, compiled and then installed. So you need a C compiler for installation.* Alternatively you can adjust setup.py and remove the cytonize part.


### Dependencies
* RPi.GPIO
* spidev
* numpy
* pillow


## Usage 
Unlike the original Adafruit_Python_ILI9341 library, this library only has a display method which expects a pillow image object and optional a window where to paint the passed image.

Example:

    from ILI9341 import ILI9341
    disp = ILI9341( 
        port         = 0,    # propably 0 (primary SPI / SPI0)
        cs           = 0,    # cs 0 / 1 from spidev or a pin number
        dc           = 20,   # data / command pin
        rst          = 26,   # reset pin
    )
    disp.begin()
    disp.set_rotation(1)

    Image.new('RGBA', disp.width, disp.height)
    disp.display(image)

    # display with window / partial update
    Image.new('RGBA', (20, 20) )
    disp.display(image, (100, 50, 120 - 1, 70 - 1))

### Differences

* Replaced adafruits SPI/GPIO and replaced it with spidev/RPi.GPIO.
* Uses spidev.writebytes2 which accept large lists and accepts numpy arrays, which offers much better performance (according to https://pypi.org/project/spidev/).
    * Therefore removed any coding for transforming the numpy array to a list.
* Possibility to pass a window into display function to allow partial redraws.
* Ported display rotation functionality from Adafruits Arduino ILI9341 library.
* Added functionality for enabling / disabling the display.
    * Disabling means switching the display of and send it to sleep, and vice versa.
* Added a software reset, if the reset pin is not passed. But it is highly recommended to connect the reset pin.
* Experimental backlight functionality:
    * Unfortunately, I cannot test the backlight functionality because the backlight of my module is directly hard wired to a pin and not to the ILI9341. But this is propably the case for most modules. But I left my experimental coding in anyway.
* Improved internal functions a bit

