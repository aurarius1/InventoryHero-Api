from  flask import Blueprint


class HelloWorld(Blueprint):

    def __init__(self, name, import_name, app, url_prefix, *args):
        self.app = app
        super(HelloWorld, self).__init__(name=name, import_name=import_name, url_prefix=url_prefix, *args)

        @self.route('/', methods=["GET"])
        def hello():
            return {'hello': 'world'}