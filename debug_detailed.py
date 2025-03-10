import traceback
import sys
import os

# 打印当前工作目录和Python路径
print(f'Current working directory: {os.getcwd()}')
print(f'Python path: {sys.path}')

try:
    # 尝试导入各个模块，逐步检查
    print('Importing modules...')
    import fastapi
    print('FastAPI imported successfully')
    import uvicorn
    print('Uvicorn imported successfully')
    import sqlalchemy
    print('SQLAlchemy imported successfully')
    
    # 尝试导入项目模块
    print('Importing project modules...')
    import models
    print('Models imported successfully')
    import utils
    print('Utils imported successfully')
    
    # 尝试导入并运行主应用
    print('Importing main app...')
    from main import app
    print('Successfully imported app')
    
    # 运行应用
    print('Starting application...')
    uvicorn.run(app, host='0.0.0.0', port=8000)
except Exception as e:
    print(f'Error: {e}')
    traceback.print_exc()