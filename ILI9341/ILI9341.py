# Modified version of Adafruit ILI9341 implementation without Adafruit GPIO/SPI
# and with optional additional SPI CS Pin

# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.



import numbers
import time

import numpy as np

from PIL import Image

import RPi.GPIO as GPIO
import spidev



# Constants for interacting with display registers.
ILI9341_TFTWIDTH    = 320
ILI9341_TFTHEIGHT   = 240

ILI9341_NOP         = 0x00
ILI9341_SWRESET     = 0x01
ILI9341_RDDID       = 0x04
ILI9341_RDDST       = 0x09

ILI9341_SLPIN       = 0x10
ILI9341_SLPOUT      = 0x11
ILI9341_PTLON       = 0x12
ILI9341_NORON       = 0x13

ILI9341_RDMODE      = 0x0A
ILI9341_RDMADCTL    = 0x0B
ILI9341_RDPIXFMT    = 0x0C
ILI9341_RDIMGFMT    = 0x0A
ILI9341_RDSELFDIAG  = 0x0F

ILI9341_INVOFF      = 0x20
ILI9341_INVON       = 0x21
ILI9341_GAMMASET    = 0x26
ILI9341_DISPOFF     = 0x28
ILI9341_DISPON      = 0x29

ILI9341_CASET       = 0x2A
ILI9341_PASET       = 0x2B
ILI9341_RAMWR       = 0x2C
ILI9341_RAMRD       = 0x2E

ILI9341_PTLAR       = 0x30
ILI9341_MADCTL      = 0x36
ILI9341_PIXFMT      = 0x3A

ILI9341_WRDISBV     = 0x51
ILI9341_RDDISBV     = 0x52
ILI9341_WRCTRLD     = 0x53
ILI9341_RDCTRLD     = 0x54

ILI9341_FRMCTR1     = 0xB1
ILI9341_FRMCTR2     = 0xB2
ILI9341_FRMCTR3     = 0xB3
ILI9341_INVCTR      = 0xB4
ILI9341_DFUNCTR     = 0xB6

ILI9341_BLCTRL8     = 0xBF


ILI9341_PWCTR1      = 0xC0
ILI9341_PWCTR2      = 0xC1
ILI9341_PWCTR3      = 0xC2
ILI9341_PWCTR4      = 0xC3
ILI9341_PWCTR5      = 0xC4
ILI9341_VMCTR1      = 0xC5
ILI9341_VMCTR2      = 0xC7

ILI9341_RDID1       = 0xDA
ILI9341_RDID2       = 0xDB
ILI9341_RDID3       = 0xDC
ILI9341_RDID4       = 0xDD

ILI9341_GMCTRP1     = 0xE0
ILI9341_GMCTRN1     = 0xE1

ILI9341_PWCTR6      = 0xFC

ILI9341_BLACK       = 0x0000
ILI9341_BLUE        = 0x001F
ILI9341_RED         = 0xF800
ILI9341_GREEN       = 0x07E0
ILI9341_CYAN        = 0x07FF
ILI9341_MAGENTA     = 0xF81F
ILI9341_YELLOW      = 0xFFE0
ILI9341_WHITE       = 0xFFFF

ILI9341_MADCTL_MY  = 0x80  # < Bottom to top
ILI9341_MADCTL_MX  = 0x40  # < Right to left
ILI9341_MADCTL_MV  = 0x20  # < Reverse Mode
ILI9341_MADCTL_ML  = 0x10  # < LCD refresh Bottom to top
ILI9341_MADCTL_RGB = 0x00  # < Red-Green-Blue pixel order
ILI9341_MADCTL_BGR = 0x08  # < Blue-Green-Red pixel order
ILI9341_MADCTL_MH  = 0x04  # < LCD refresh right to left



#def color565(r : int, g : int, b : int):
#    """Convert red, green, blue components to a 16-bit 565 RGB value. Components
#    should be values 0 to 255.
#    """
#    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def image_to_data(image : Image) :
    """Generator function to convert a PIL image to 16-bit 565 RGB bytes."""
    #NumPy is much faster at doing this. NumPy code provided by:
    #Keith (https://www.blogger.com/profile/02555547344016007163)
    pb = np.array(image.convert('RGB')).astype('uint16')
    color = ((pb[:,:,0] & 0xF8) << 8) | ((pb[:,:,1] & 0xFC) << 3) | (pb[:,:,2] >> 3)
    #return np.dstack(((color >> 8) & 0xFF, color & 0xFF)).flatten().tolist()
    return np.dstack(((color >> 8) & 0xFF, color & 0xFF)).ravel().tolist()


class ILI9341(object):
    """Representation of an ILI9341 TFT LCD."""

    def __init__(self, port, cs, dc, rst=None, width=ILI9341_TFTWIDTH, height=ILI9341_TFTHEIGHT):
        """Create an instance of the display using SPI communication.  Must
        provide the GPIO pin number for the D/C pin, spi port and cs (driver or GPIO).  Can
        optionally provide the GPIO pin number for the reset pin as the rst
        parameter.
        """
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        self._dc = dc
        self._rst = rst
        self._cs = cs
        self._spi = spidev.SpiDev(port, self._cs if self._cs <= 1 else 0)
        if self._cs > 1:
            self._spi.no_cs = True
            GPIO.setup(self._cs, GPIO.OUT)
            GPIO.output(self._cs, GPIO.HIGH)

        self.width = width
        self.height = height

        # Set DC as output.
        GPIO.setup(self._dc, GPIO.OUT)
        # Setup reset as output (if provided).
        if self._rst is not None:
            GPIO.setup(rst, GPIO.OUT)

        # Set SPI to mode 0, MSB first.
        self._spi.mode = 0
        self._spi.lsbfirst = False
        self._spi.max_speed_hz = 64000000


    def send(self, data, is_data=True) -> None:
        """Write a byte or array of bytes to the display. Is_data parameter
        controls if byte should be interpreted as display data (True) or command
        data (False).
        """
        # Set DC low for command, high for data.
        GPIO.output(self._dc, is_data)
        # Convert scalar argument to list so either can be passed as parameter.
        if isinstance(data, numbers.Number):
            data = [data & 0xFF]

        if self._cs > 1:
            GPIO.output(self._cs, GPIO.LOW)

        self._spi.writebytes2(data)

        if self._cs > 1:
            GPIO.output(self._cs, GPIO.HIGH)


    def command(self, cmd, params=None) -> None:
        """Write a byte or array of bytes to the display as command data."""
        self.send(cmd, False)
        if params is not None:
            self.send(params, True)


    def data(self, data) -> None:
        """Write a byte or array of bytes to the display as display data."""
        self.send(data, True)


    def reset(self) -> None:
        """Reset the display, if reset pin is connected."""
        if self._rst is not None:
            GPIO.output(self._rst, GPIO.HIGH)
            time.sleep(0.005)
            GPIO.output(self._rst, GPIO.LOW)
            time.sleep(0.02)
            GPIO.output(self._rst, GPIO.HIGH)
            time.sleep(0.150)
        else:
            self.command(ILI9341_SWRESET)
            time.sleep(0.005)


    def _init(self) -> None:
        # Initialize the display.  Broken out as a separate function so it can
        # be overridden by other displays in the future.
        self.command(0xEF, [0x03, 0x80, 0x02])
        self.command(0xCF, [0x00, 0XC1, 0X30])
        self.command(0xED, [0x64, 0x03, 0X12, 0X81])
        self.command(0xE8, [0x85, 0x00, 0x78])
        self.command(0xCB, [0x39, 0x2C, 0x00, 0x34, 0x02])
        self.command(0xF7, [0x20])
        self.command(0xEA, [0x00, 0x00])
        self.command(ILI9341_PWCTR1, [0x23])               # Power control, VRH[5:0]
        self.command(ILI9341_PWCTR2, [0x10])               # Power control, SAP[2:0];BT[3:0]
        self.command(ILI9341_VMCTR1, [0x3e, 0x28])         # VCM control
        self.command(ILI9341_VMCTR2, [0x86])               # VCM control2, --
        self.command(ILI9341_MADCTL, [0x48])               #  Memory Access Control
        self.command(ILI9341_PIXFMT, [0x55])
        self.command(ILI9341_FRMCTR1, [0x00, 0x18])
        self.command(ILI9341_DFUNCTR, [0x08, 0x82, 0x27])  #  Display Function Control
        self.command(0xF2, [0x00])                         #  3Gamma Function Disable

        self.command(ILI9341_GAMMASET, [0x01])             # Gamma curve selected

        self.command(ILI9341_GMCTRP1, [0x0F,0x31, 0x2B, 0x0C, 0x0E, 0x08, 0x4E, 0xF1, 0x37, 0x07, 0x10, 0x03, 0x0E, 0x09, 0x00]) # Set pos. Gamma
        self.command(ILI9341_GMCTRN1, [0x00, 0x0E, 0x14, 0x03, 0x11, 0x07, 0x31, 0xC1, 0x48, 0x08, 0x0F, 0x0C, 0x31, 0x36, 0x0F]) # Set neg. Gamma

        # 0x2c = 101100 => BCTRL = 1, DD = 1, BL = 1
        # 0x28 = 101000 => BCTRL = 1, DD = 1, BL = 0
        # 0x20 = 100000 => BCTRL = 1, DD = 0, BL = 0
        #self.command(ILI9341_WRCTRLD, [0x28])             # Write CTRL Display 

        self.command(ILI9341_SLPOUT)    # Exit Sleep
        time.sleep(0.120)
        self.command(ILI9341_DISPON)    # Display on


    def begin(self) -> None:
        """Initialize the display. Should be called once before other calls that
        interact with the display are called.
        """
        self.reset()
        self._init()


    def set_window(self, x0 : int = 0, y0 : int = 0, x1=None, y1=None) -> None:
        """Set the pixel address window for proceeding drawing commands. x0 and
        x1 should define the minimum and maximum x pixel bounds.  y0 and y1
        should define the minimum and maximum y pixel bound.  If no parameters
        are specified the default will be to update the entire display from 0,0
        to 239,319.
        """
        if x1 is None:
            x1 = self.width-1
        if y1 is None:
            y1 = self.height-1
        self.command(ILI9341_CASET)        # Column addr set
        self.data(x0 >> 8)
        self.data(x0)                      # XSTART
        self.data(x1 >> 8)
        self.data(x1)                      # XEND
        self.command(ILI9341_PASET)        # Row addr set
        self.data(y0 >> 8)
        self.data(y0)                      # YSTART
        self.data(y1 >> 8)
        self.data(y1)                      # YEND
        self.command(ILI9341_RAMWR)        # write to RAM


    def display(self, image, window=None):
        """Write the display buffer or provided image to the hardware.  If no
        image parameter is provided the display buffer will be written to the
        hardware.  If an image is provided, it should be RGB format and the
        same dimensions as the display hardware.
        """
        if window is None:
            # Set address bounds to entire display.
            self.set_window()
        else:
            self.set_window(*window)

        # Convert image to array of 16bit 565 RGB data bytes.
        # Unfortunate that this copy has to occur, but the SPI byte writing
        # function needs to take an array of bytes and PIL doesn't natively
        # store images in 16-bit 565 RGB format.
        self.data(image_to_data(image))


    def set_backlight(self, value : int = 255) -> None:
        #Experimental, not supported when backlight not connected to ILI9341
        """Set the backlight on/off."""
        if isinstance(value, bool):
            self.command(ILI9341_BLCTRL8)
            if value:
                self.data(0x04) # 1 0 0  -> LEDONR, LEDONPOL, LEDPWMPOL
            else:
                self.data(0x00) # 0 0 0  -> LEDONR, LEDONPOL, LEDPWMPOL

        elif isinstance(value, int):
            if value == 0:
                self.set_backlight(False)
            else:
                self.command(ILI9341_WRDISBV, [(0xFF * value / 100)] ) # 255 in relation to 100
                self.set_backlight(True)


    def set_rotation(self, m : int) -> None:
        rotation = m % 4; # can't be higher than 3
        if rotation == 0:
            m = (ILI9341_MADCTL_MX | ILI9341_MADCTL_BGR)
            self.width = ILI9341_TFTWIDTH
            self.height = ILI9341_TFTHEIGHT
        
        elif rotation == 1:
            m = (ILI9341_MADCTL_MV | ILI9341_MADCTL_BGR)
            self.width = ILI9341_TFTHEIGHT
            self.height = ILI9341_TFTWIDTH

        elif rotation == 2:
            m = (ILI9341_MADCTL_MY | ILI9341_MADCTL_BGR)
            self.width = ILI9341_TFTWIDTH
            self.height = ILI9341_TFTHEIGHT

        elif rotation == 3:
            m = (ILI9341_MADCTL_MX | ILI9341_MADCTL_MY | ILI9341_MADCTL_MV | ILI9341_MADCTL_BGR)
            self.width = ILI9341_TFTHEIGHT
            self.height = ILI9341_TFTWIDTH
        else:
            return

        self.command(ILI9341_MADCTL, m)


    def enable(self) -> None:
        self.command(ILI9341_SLPOUT)    # Exit Sleep
        time.sleep(0.120)
        self.command(ILI9341_DISPON)    # Display on
        time.sleep(0.005) #?


    def disable(self) -> None:
        self.command(ILI9341_DISPOFF)  # Display off
        time.sleep(0.005) #?
        self.command(ILI9341_SLPIN)    # Enter Sleep
        time.sleep(0.120)

