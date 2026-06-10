from mangum import Mangum

from lapwise.main import app

handler = Mangum(app, lifespan="off")
