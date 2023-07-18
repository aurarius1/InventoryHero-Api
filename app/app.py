from flask import Flask
import os

from endpoints.HelloWorld import HelloWorld

app = Flask(__name__)
helloworld = HelloWorld('hello_world', __name__, app=app, url_prefix="/api/v1")
app.register_blueprint(helloworld)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)