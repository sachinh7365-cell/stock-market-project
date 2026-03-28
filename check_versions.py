import sys
try:
    import tensorflow as tf
    print('tensorflow', tf.__version__)
except Exception as e:
    print('tensorflow import error:', e)
try:
    from tensorflow import keras
    print('keras', keras.__version__)
except Exception as e:
    print('keras import error:', e)
print('python', sys.version)
