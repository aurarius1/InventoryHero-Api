from flask import Blueprint


class HelloWorld(Blueprint):

    def __init__(self, name, import_name, application, db, url_prefix, *args):
        self.app = application
        self.db = db
        super(HelloWorld, self).__init__(name=name, import_name=import_name, url_prefix=url_prefix, *args)

        @self.route('/', methods=["GET"])
        def hello():

            return {'hello': 'world'}