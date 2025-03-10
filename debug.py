import traceback
import sys

try:
    from main import app
    print('Successfully imported app')
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
except Exception as e:
    print(f'Error: {e}')
    traceback.print_exc()