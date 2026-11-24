import uvicorn
from app.config import HOST,PORT
if __name__=='__main__': uvicorn.run('app.api:app',host=HOST,port=PORT)
