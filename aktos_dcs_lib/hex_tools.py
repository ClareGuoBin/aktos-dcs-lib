__author__ = 'ceremcem'
import re

def hex_from_readable(string):
    string = re.sub(r"[\n\s]+", " ", string)
    chars = [i for i in string.split(" ") if len(i) > 0]
    print "chars: ", chars
    chars_hex = map(lambda x: int(x, 16), chars)
    return ''.join(map(chr, chars_hex))

def readable_from_hex(string):
    l = map(ord, string)
    l = map(lambda x: hex(x)[2:].zfill(2).upper(), l)
    return ' '.join(l)
