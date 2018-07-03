#!/usr/bin/env python

from __future__ import print_function
import time
import sys
import usb.core
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


#####################################################################################
## sudo apt-get install python-usb
## or
## sudo -H python3 -m pip install pyusb

## install Dejavu TTF fonts
# sudo apt-get install ttf-dejavu

## install Python Pillow package
# sudo -H pip3 install pillow -U

#####################################################################################

# idVendor=0416, idProduct=5020
VENDOR_ID  = 0x0416
PRODUCT_ID = 0x5020

# bitmap dimension
WIDTH  = 448  # tested up to 400 pixels
HEIGHT = 12

message = '3-Jul-2018 Thailand cave rescue: Boys found alive after 9 days..'

#####################################################################################

def getBitmap( str, font, img_w, img_h, xoff=0, yoff=0 ):
    image = Image.new( '1', (img_w, img_h) )
    draw = ImageDraw.Draw(image)
    text_width, text_height = draw.textsize( str, font=font )
    print ('image width x height: {0}x{1}'.format(image.width, image.height) )
    print ('text  width x height: {0}x{1}'.format(text_width, text_height) )
    print ('message: "{0}"'.format( str ) )
    if text_width > img_w:
        print ( 'Text too long!!!' )
        return None

    pos = (xoff, (HEIGHT-text_height)/2 + yoff )
    draw.text( pos, str, fill=1, font=font)
    pixels = image.load()

    data = []
    for x in range( 0, img_w, 8 ):
        for y in range( img_h ):
            b = 0
            for i in range(8):
                b += pixels[x+i,y] << (7-i)
            data.append( b )

    return data

####################################################################################

def connectBadge( vid=VENDOR_ID, pid=PRODUCT_ID ):
    interface = None
    interface_number = -1

    device = usb.core.find( idVendor=vid, idProduct=pid )
    device.reset()
    time.sleep(0.1)

    config = device.get_active_configuration()

    for interface in config:
        if interface.bInterfaceClass == 0x3:  # HID device
            interface_number = interface.bInterfaceNumber
            break
    try:
        if device.is_kernel_driver_active(interface_number):
            device.detach_kernel_driver(interface_number)
    except Exception as e:
        print(e)
        return None

    ep_in, ep_out = None, None
    for ep in interface:
        if ep.bEndpointAddress == 0x81:
            ep_in = ep
        else:
            ep_out = ep

    return ep_out, ep_in

####################################################################################

ep_out,_ = connectBadge()

if ep_out == None:
    print('USB Endpoint error !!!')
    sys.exit(-1)

#font = ImageFont.load_default()
#font_name = '/usr/share/fonts/truetype/freefont/FreeSans.ttf'
font_name = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSansMono.ttf'
font = ImageFont.truetype( font_name, 11 )

#str = '+0123456789ABCDEF++0123456789ABCDEF+++0123456789ABCDEF...'

p = getBitmap( message, font, WIDTH, HEIGHT, 0, 0 )

if p == None:
    print('Bitmap error !!!')
    sys.exit(-1)

nb = int(WIDTH/8)  # num bytes per row
num_bytes = (nb * HEIGHT)

HEAD_PKT =  b'\x77\x61\x6e\x67\x00\x00\x00\x00\x40\x40\x47\x48\x40\x44\x46\x47' \
         +  b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
         +  b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
         +  b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

try:
    pkt = bytearray( HEAD_PKT )
    cfg_speed = (5 << 4) # 0 (slowest)..7 (fastest)
    cfg_mode  = (0x0) # 0x0=moving left, 0x1=moving right, 0x2=moving top, 0x3=moving bottom
    pkt[8]  = cfg_speed | cfg_mode # M1 config
    pkt[17] = nb    # 17=M1, 19=M2, 21=M3, 23=M4, 25=M5, 27=M6, 29=M7, 31=M8
    ep_out.write( bytes(pkt) )

except usb.core.USBError as e:
    print ("#1 Write USBError: " + str(e))
time.sleep(0.2)

try:
    ep_out.write( p )
except usb.core.USBError as e:
    print ("#2 Write USBError: " + str(e))

print ('done')

