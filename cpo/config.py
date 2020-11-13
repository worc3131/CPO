
log_size = 50
logging = 0
# port = 0
# suppress = ''

def get(key, default):
    return getattr(locals(), key, default)