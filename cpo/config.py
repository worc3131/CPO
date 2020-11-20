
log_size = 50
logging = 0
port = 0
# suppress = ''

# poolKIND ='ADAPTIVE'
# poolMAX = 1024
# poolREPORT = False
# poolG = 0
# poolM = 6
# poolK = 0

def get(key, default):
    return getattr(locals(), key, default)