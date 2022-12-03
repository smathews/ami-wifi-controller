# Use to override ulogging library used for the default logger by picoweb

def info(s):
    print(s)

def error(s):
    info(s)

def exc(s):
    info(s)

def debug(s, *args):
    info(s % args)