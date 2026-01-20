import joblib
import pickle
import warnings
warnings.filterwarnings('ignore')

print("Testing joblib...")
try:
    data = joblib.load('best_asd_mobilenetv2/asd_model.pkl')
    print('✓ SUCCESS - Loaded with joblib')
    print('Keys:', list(data.keys()))
except Exception as e:
    print('✗ Joblib failed:', str(e)[:100])

print("\nTesting pickle with numpy handling...")
try:
    import numpy as np
    # Try to fix the numpy random state issue
    import numpy.random as nprand
    # Register the BitGenerator if missing
    f = open('best_asd_mobilenetv2/asd_model.pkl', 'rb')
    data = pickle.load(f, encoding='bytes')
    print('✓ SUCCESS - Loaded with pickle')
    print('Keys:', list(data.keys()))
    f.close()
except Exception as e:
    print('✗ Pickle failed:', str(e)[:100])
