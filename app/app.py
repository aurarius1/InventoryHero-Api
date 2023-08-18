import os, logging

from flask import Flask
from flask_session import Session

from endpoints.HelloWorld import HelloWorld
from endpoints.User import User
from endpoints.ProductEndpoint import ProductEndpoint
from endpoints.StorageEndpoint import StorageEndpoint
from flask_config import get_config
from database import db

app = Flask(__name__)
app.config.from_object(get_config())
db.init_app(app)
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_logger.handlers)
app.logger.setLevel(logging.INFO)

url_prefix = "/api/v1"

helloworld = HelloWorld('hello_world', __name__, application=app, db=db, url_prefix=url_prefix)
user = User('user', __name__, application=app, db=db, url_prefix=url_prefix)
products = ProductEndpoint('product_endpoint', __name__, application=app, db=db, url_prefix=url_prefix )
storage = StorageEndpoint('storage_endpoint', __name__, application=app, db=db, url_prefix=url_prefix)
app.register_blueprint(helloworld)
app.register_blueprint(user)
app.register_blueprint(products)
app.register_blueprint(storage)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    with app.app_context():
        from models.User import User
        from models.StorageContainer import Box, Location
        from models.Product import Product, ProductContainerMapping
        db.create_all()
    Session(app)
    app.run(debug=True, host='0.0.0.0', port=port)
else:
    with app.app_context():
        db.create_all()
    Session(app)
