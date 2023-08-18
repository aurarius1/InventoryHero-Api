import sqlalchemy.exc
from flask import Blueprint, request, session
from models.User import User as ApplicationUser, Household, HouseholdMembers
from decorators import authorize
import bcrypt


class User(Blueprint):
    def __init__(self, name, import_name, application, db, url_prefix, *args):
        self.app = application
        self.db = db

        url_prefix += ("" if url_prefix.endswith("/") else "/") + "user"

        super(User, self).__init__(name=name, import_name=import_name, url_prefix=url_prefix, *args)

        @self.route('/create_user', methods=["POST"])
        def create_user():
            data = dict(request.form)

            username = data.get("username", None)
            if username is None:
                self.app.logger.error("No or invalid username provided")
                return {"status": "username is invalid"}, 400

            password = data.get("password", None)
            if password is None:
                self.app.logger.error("No password provided")
                return {"status": "password is invalid"}, 400
            salt = bcrypt.gensalt()

            email = data.get("email", None)
            if email is None:
                self.app.logger.error("No or invalid email provided")
                return {"status": "email is invalid"}, 400

            password = password.encode('utf-8')
            password = bcrypt.hashpw(password, salt)

            self.app.logger.info({
                "username": username,
                "password": password,
                "email": email
            })
            user = ApplicationUser(username=username, email=email, password=password)
            try:
                self.db.session.add(user)
                self.db.session.commit()
            except sqlalchemy.exc.IntegrityError as e:
                self.app.logger.error(e)
                return {'status': f'username {username} already in use'}, 500
            return {'status': f'user {username} successfully created'}, 200

        @self.route('/create_household', methods=["POST"])
        @authorize
        def create_household():
            data = dict(request.form)

            household_name = data.get("name", None)
            if household_name is None:
                return {"status": "No or invalid household name given"}, 400

            user = ApplicationUser.query.filter_by(username=session.get("username")).first()
            if user is None:
                self.app.logger.error("User does not exist")
                return {"status": "username does not exist"}, 404

            household = Household(name=household_name, creator=user.id)
            self.db.session.add(household)
            self.db.session.commit()

            member = HouseholdMembers(household_id=household.id, member_id=user.id)
            self.db.session.add(member)
            self.db.session.commit()

            return {}, 200

        @self.route("/login", methods=["POST"])
        def login():
            data = dict(request.form)
            username = data.get("username", None)
            if username is None:
                self.app.logger.error("No or invalid username provided")
                return {"status": "username is invalid"}, 400

            password = data.get("password", None)
            if password is None:
                self.app.logger.error("No password provided")
                return {"status": "password is invalid"}, 400

            user = ApplicationUser.query.filter_by(username=username).first()
            if user is None:
                self.app.logger.error("User does not exist")
                return {"status": "username does not exist"}, 404

            pw_valid = bcrypt.checkpw(password.encode('utf-8'), user.password)
            if not pw_valid:
                return {"status": "username or password invalid"}, 500
            session["username"] = user.username
            return {}, 200

        @self.route("/logout", methods=["GET"])
        def logout():
            current_session = session.get("username", None)
            if current_session is None:
                return {}, 200
            session.pop("username")
            return {}, 200

        @self.route("/userpage", methods=["GET"])
        @authorize
        def userpage():
            return {'username': session.get('username')}
