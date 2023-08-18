import datetime, json

from flask import Blueprint, request, session, jsonify
from models.User import Household, User, HouseholdMembers
from models.Product import Product, ProductContainerMapping
from models.StorageContainer import Location, Box, ContainerTypes
from decorators import authorize

from endpoints.Helper import user_in_household, get_user_from_db, container_name_unique


class StorageEndpoint(Blueprint):
    def __init__(self, name, import_name, application, db, url_prefix="", *args):
        self.app = application
        self.db = db

        url_prefix += ("" if url_prefix.endswith("/") else "/") + "storage"

        super(StorageEndpoint, self).__init__(name=name, import_name=import_name, url_prefix=url_prefix, *args)

        @self.route("/get_storage", methods=["GET"])
        @authorize
        def get_storage():
            storage_type = request.args.get("type", None)

            username = session.get("username", None)
            self.app.logger.info(username)
            user, ret = get_user_from_db(username)
            if user is None:
                return ret

            if storage_type is None:
                return {"status": "no storage type is given"}, 400

            try:
                storage_type = ContainerTypes(int(storage_type))
            except ValueError as e:
                self.app.logger.error(e)
                return {"status": "no valid storage type is given"}, 402

            storage_id = request.args.get("storage_id", None)
            if storage_id is None:
                return {"status": "no storage is given"}, 400
            try:
                storage_id = int(storage_id)
            except ValueError as e:
                self.app.logger.error(e)
                return {"status": "no valid storage is given"}, 400

            if storage_type == ContainerTypes.Box:
                storage_container = Box.query.filter_by(id=storage_id).first()
                if storage_container is None:
                    return {"status": "invalid box id given"}, 400
            elif storage_type == ContainerTypes.Location:
                storage_container = Location.query.filter_by(id=storage_id).first()
                if storage_container is None:
                    return {"status": "invalid room id given"}, 400
            else:
                return {"status": "no valid storage type is given"}, 400

            in_household, ret = user_in_household(user.id, storage_container.household_id)
            if not in_household:
                return ret

            return jsonify(storage_container), 200

        @self.route("/get_all_storage", methods=["GET"])
        @authorize
        def get_all_storage():
            storage_type = request.args.get("type", None)

            username = session.get("username", None)
            self.app.logger.info(username)
            user, ret = get_user_from_db(username)
            if user is None:
                return ret

            if storage_type is None:
                return {"status": "no storage type is given"}, 400

            try:
                storage_type = ContainerTypes(int(storage_type))
            except ValueError as e:
                self.app.logger.error(e)
                return {"status": "no valid storage type is given"}, 402

            household_id = request.args.get("household_id", None)
            if household_id is None:
                return {"status": "no household is given"}, 400
            try:
                household_id = int(household_id)
            except ValueError as e:
                self.app.logger.error(e)
                return {"status": "no valid household is given"}, 400

            in_household, _ = user_in_household(user.id, household_id)
            if not in_household:
                return {"status": "user does not belong to given household / household does not exist"}, 400

            if storage_type == ContainerTypes.Box:
                storage_container = Box.query.filter_by(household_id=household_id).all()
                if storage_container is None:
                    return {"status": "invalid box id given"}, 400
            elif storage_type == ContainerTypes.Location:
                storage_container = Location.query.filter_by(household_id=household_id).all()
                if storage_container is None:
                    return {"status": "invalid room id given"}, 400
            else:
                return {"status": "no valid storage type is given"}, 400

            return jsonify(storage_container), 200

        @self.route("/add_storage", methods=["POST"])
        @authorize
        def add_storage():
            data = dict(request.form)
            storage_type = data.pop("type", None)

            username = session.get("username", None)
            self.app.logger.info(username)
            user, ret = get_user_from_db(username)
            if user is None:
                return ret

            if storage_type is None:
                return {"status": "no storage type is given"}, 400

            try:
                storage_type = ContainerTypes(int(storage_type))
            except ValueError as e:
                self.app.logger.error(e)
                return {"status": "no valid storage type is given"}, 402

            household_id = data.pop("household", None)
            if household_id is None:
                return {"status": "no household is given"}, 400
            try:
                household_id = int(household_id)
            except ValueError as e:
                self.app.logger.error(e)
                return {"status": "no valid household is given"}, 400

            in_household, _ = user_in_household(user.id, household_id)
            if not in_household:
                return {"status": "user does not belong to given household / household does not exist"}, 400

            storage_name = data.pop("name", "")
            if storage_name == "":
                return {"status": "invalid name give"}, 400

            if storage_type == ContainerTypes.Box:
                location_id = data.pop("location", None)
                if location_id is not None:
                    try:
                        location_id = int(location_id)
                    except ValueError as e:
                        self.app.logger.error(e)
                        return {"status": "invalid location supplied"}, 400
                    location = Location.query.filter_by(id=location_id).first()
                    in_household, ret = user_in_household(user.id, location.household_id)
                    if not in_household or location.household_id != household_id:
                        return {"status": "given location does not belong to users household / does not exist"}, 400

                unique = Box.query.filter_by(household_id=household_id, name=storage_name).first() is None
                if not unique:
                    return {"status": "name needs to be unique within your household"}, 400

                new_box = Box(name=storage_name, household_id=household_id, location_id=location_id)
                self.db.session.add(new_box)
            elif storage_type == ContainerTypes.Location:
                unique = Location.query.filter_by(household_id=household_id, name=storage_name).first() is None
                if not unique:
                    return {"status": "name needs to be unique within your household"}, 400
                new_location = Location(name=storage_name, household_id=household_id)
                self.db.session.add(new_location)
            else:
                return {"status": "no valid storage type is given"}, 400
            self.db.session.commit()
            return {}, 200

        @self.route("/update_storage", methods=["POST"])
        @authorize
        def update_storage():
            data = dict(request.form)
            storage_type = data.pop("type", None)

            username = session.get("username", None)
            self.app.logger.info(username)
            user, ret = get_user_from_db(username)
            if user is None:
                return ret

            if storage_type is None:
                return {"status": "no storage type is given"}, 400

            try:
                storage_type = ContainerTypes(int(storage_type))
            except ValueError as e:
                self.app.logger.error(e)
                return {"status": "no valid storage type is given"}, 400

            storage_id = data.pop("storage", None)
            if storage_id is None:
                return {"status": "no storage given"}, 400

            try:
                storage_id = int(storage_id)
            except ValueError as e:
                self.app.logger.error(e)
                return {"status": "invalid storage given"}, 400

            if storage_type == ContainerTypes.Box:
                container = Box.query.filter_by(id=storage_id).first()
            elif storage_type == ContainerTypes.Location:
                container = Location.query.filter_by(id=storage_id).first()
            else:
                return {"status": "invalid storage type"}, 400

            if container is None:
                return {"status": "invalid storage type"}, 400

            in_household, _ = user_in_household(user.id, container.household_id)
            if not in_household:
                return {"status": "user does not belong to given household / household does not exist"}, 400

            new_name = data.pop("name", None)
            if new_name is not None:
                if container_name_unique(container.household_id, container.id, storage_type, new_name):
                    container.name = new_name
                else:
                    return {"status": "name must be unique within one household!"}, 400
            if storage_type == ContainerTypes.Box:
                new_location = data.pop("location", None)
                if new_location is not None:
                    try:
                        new_location = int(new_location)
                    except ValueError as e:
                        self.app.logger.error(e)
                        return {"status": "invalid new location given"}, 400
                    if new_location == -1:
                        new_location = None
                    else:
                        location = Location.query.filter_by(id = new_location).first()
                        if location is None:
                            return {"status": "new location not found"}, 400
                        in_household, ret = user_in_household(user.id, location.household_id)
                        if not in_household:
                            return ret

                    container.location_id = new_location

            self.db.session.commit()
            return {}, 200

        @self.route("/delete_storage", methods=["DELETE"])
        @authorize
        def delete_storage():
            storage_type = request.args.get("type", None)

            username = session.get("username", None)
            self.app.logger.info(username)
            user, ret = get_user_from_db(username)
            if user is None:
                return ret

            if storage_type is None:
                return {"status": "no storage type is given"}, 400

            try:
                storage_type = ContainerTypes(int(storage_type))
            except ValueError as e:
                self.app.logger.error(e)
                return {"status": "no valid storage type is given"}, 400

            storage_id = request.args.get("storage", None)
            if storage_id is None:
                return {"status": "Noting to delete"}, 200

            try:
                storage_id = int(storage_id)
            except ValueError as e:
                self.app.logger.error(e)
                return {"statust": "no valid storage given"}, 400

            if storage_type == ContainerTypes.Box:
                container = Box.query.filter_by(id=storage_id).first()
            elif storage_type == ContainerTypes.Location:
                container = Location.query.filter_by(id=storage_id).first()
            else:
                return {"status": "no valid storage type is given"}, 400

            if container is None:
                return {"status": "storage not found"}, 400

            in_household, ret = user_in_household(user.id, container.household_id)
            if not in_household:
                return ret

            self.db.session.delete(container)
            self.db.session.commit()

            return {}, 200