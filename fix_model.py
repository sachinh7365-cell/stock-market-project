import h5py
import json
import shutil
import sys

MODEL_PATH = 'stock_dl_model.h5'
BACKUP_PATH = MODEL_PATH + '.bak'

shutil.copyfile(MODEL_PATH, BACKUP_PATH)
print(f'Backup created at {BACKUP_PATH}')

with h5py.File(MODEL_PATH, 'r+') as f:
    mc = None
    source = None
    if 'model_config' in f.attrs:
        mc = f.attrs['model_config']
        if isinstance(mc, bytes):
            mc = mc.decode('utf-8')
        source = 'attrs'
    elif 'model_config' in f:
        mc = f['model_config'][()]
        if isinstance(mc, bytes):
            mc = mc.decode('utf-8')
        source = 'dataset'
    else:
        print('model_config not found in HDF5 attributes or datasets')
        sys.exit(1)

    try:
        cfg = json.loads(mc)
    except Exception as e:
        print('Failed to parse model_config JSON:', e)
        sys.exit(1)

    def remove_key(obj, key):
        if isinstance(obj, dict):
            if key in obj:
                del obj[key]
            for v in obj.values():
                remove_key(v, key)
        elif isinstance(obj, list):
            for item in obj:
                remove_key(item, key)

    remove_key(cfg, 'time_major')

    new = json.dumps(cfg)
    if new != mc:
        if source == 'attrs':
            f.attrs['model_config'] = new.encode('utf-8')
        else:
            del f['model_config']
            f.create_dataset('model_config', data=new.encode('utf-8'))
        print('Removed "time_major" from model_config and updated file.')
    else:
        print('No "time_major" key found; no changes made.')

# Attempt to load the model to verify
try:
    from tensorflow.keras.models import load_model
    m = load_model(MODEL_PATH)
    print('Model loaded successfully.')
except Exception as e:
    print('Error loading model after patch:', e)
