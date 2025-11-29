import os
import sys
import django

print("--- Checking Django Environment ---")
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lims.settings')
    django.setup()
    print("Django setup successful.")
except Exception as e:
    print(f"Django setup failed: {e}")
    sys.exit(1)

print("\n--- Checking Imports ---")
try:
    import channels
    print(f"channels version: {channels.__version__}")
    import daphne
    print(f"daphne imported: {daphne}")
    import requests
    print(f"requests version: {requests.__version__}")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

print("\n--- Checking ASGI Application ---")
try:
    from lims.asgi import application
    print("ASGI application loaded successfully.")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n--- All Checks Passed ---")
