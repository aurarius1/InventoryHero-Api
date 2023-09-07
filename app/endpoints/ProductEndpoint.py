import datetime, json

from flask import Blueprint, request, session, jsonify
from models.User import Household, User, HouseholdMembers
from models.Product import Product, ProductContainerMapping
from models.StorageContainer import Location, Box, ContainerTypes
from decorators import authorize

from endpoints.Helper import user_in_household, get_user_from_db, string_to_bool, update_container_id

# TODO getLastUsedProducts


class ProductEndpoint(Blueprint):
    def __init__(self, name, import_name, application, db, url_prefix="", *args):
        self.app = application
        self.db = db

        url_prefix += ("" if url_prefix.endswith("/") else "/") + "products"

        super(ProductEndpoint, self).__init__(name=name, import_name=import_name, url_prefix=url_prefix, *args)

        @self.route("/create_product", methods=["POST"])
        @authorize
        def create_product():
            data = dict(request.form)

            product_name = data.get("name", None)
            if product_name is None:
                return {"status": "No (valid) product name given"}, 400

            household_id = data.get("household", None)
            if household_id is None:
                return {"status": "Product must be associated to a household"}, 400

            starred = string_to_bool(data.get("starred", "False"))
            creation_date = datetime.datetime.utcnow()

            location_id = data.get("location", None)
            if location_id is not None:
                location = Location.query.filter_by(id=location_id).first()
                if location is None:
                    return {"status": "Invalid location supplied"}, 400
                location_id = location.id

            box_id = data.get("box", None)
            if box_id is not None:
                box = Box.query.filter_by(id=box_id).first()
                if box is None:
                    return {"status": "Invalid box supplied"}, 400
                box_id = box.id

            amount = data.get("amount", 1)
            updated_at = creation_date

            product = Product.query.filter_by(name=product_name).first()
            if product is not None:
                return {"status": "Product already exists"}, 500

            household = Household.query.filter_by(id=household_id).first()
            if household is None:
                return {"status": "Products need to be associated to a household"}, 400

            product = Product(name=product_name, household_id=household.id, starred=starred,
                              creation_date=creation_date)
            self.db.session.add(product)
            self.db.session.flush()
            production_at_container = ProductContainerMapping(product_id=product.id, amount=amount, box_id=box_id,
                                                              location_id=location_id, updated_at=updated_at)

            self.db.session.add(production_at_container)
            self.db.session.commit()
            self.app.logger.info(f"Product: {product_name} with amount: {amount} successfully created, "
                                 f"at box: {box_id}/location: {location_id}")

            created_product = ProductContainerMapping.query.filter_by(id=production_at_container.id).first()

            return jsonify(created_product.serialize()), 200

        @self.route("/get_products", methods=["GET"])
        @authorize
        def get_products():
            box_id = request.args.get('box', None)

            location_id = request.args.get('location', None)
            household_id = request.args.get('household', None)
            get_starred = request.args.get("starred", None)
            product_id = request.args.get("product", None)
            only_product = string_to_bool(request.args.get("product_only", "false"))
            self.app.logger.info(only_product)
            username = session.get("username", None)
            self.app.logger.info(username)
            user, ret = get_user_from_db(username)
            if user is None:
                return ret

            if household_id is None:
                return {"status": "Please specify a household"}, 400
            else:
                household = HouseholdMembers.query.filter_by(household_id=household_id, member_id=user.id).first()
                if household is None:
                    return {"status": "User is not a member of the given household"}, 400

            if box_id is not None:
                self.app.logger.info("LISTING PRODUCTS IN BOX")
                try:
                    box_id = int(box_id)
                except ValueError as e:
                    self.app.logger.error(e)
                    return {"status": "invalid_box_id"}, 400
                self.app.logger.info(box_id)
                box = Box.query.filter_by(id=box_id, household_id=household_id).first()
                if box is None:
                    return {"status": "box_not_found"}, 400
            elif location_id is not None:
                self.app.logger.info("LISTING PRODUCTS IN LOCATION")
                try:
                    location_id = int(location_id)
                except ValueError as e:
                    self.app.logger.error(e)
                    return {"status": "invalid_location_id"}, 400
                location = Location.query.filter_by(id=location_id, household_id=household_id).first()
                if location is None:
                    return {"status": "location does not belong to your household"}, 400

            products = Product.query.filter_by(household_id=household_id)
            if get_starred is not None:
                products = products.filter(Product.starred)
            if product_id is not None:
                products = products.filter(Product.id == product_id)

            products = products.all()

            if only_product:
                return jsonify(products), 200

            result = []
            self.app.logger.info(products)
            for product in products:
                mappings = product.mappings
                self.app.logger.info(mappings)
                if box_id is not None:
                    mappings = [mapping for mapping in mappings if mapping.box_id == box_id]
                elif location_id is not None:
                    mappings = [mapping for mapping in mappings if mapping.location_id == location_id]

                if len(mappings) == 0:
                    continue
                storage_locations = [storage_location.serialize() for storage_location in mappings]
                result.extend(storage_locations)
            self.app.logger.info(result)
            return jsonify(result), 200

        @self.route("/change_product_stock", methods=["POST"])
        @authorize
        def change_product_stock():
            data = dict(request.form)

            username = session.get("username", None)
            self.app.logger.info(username)
            user, ret = get_user_from_db(username)
            if user is None:
                return ret

            product_mapping_id = data.get("product", None)
            if product_mapping_id is None:
                return {"status": "No product given"}, 400

            mapping = ProductContainerMapping.query.filter_by(id=product_mapping_id).first()

            if mapping is None:
                return {"status": "Product not found"}, 404
            self.app.logger.info(mapping.product)
            in_household, ret = user_in_household(user.id, mapping.product.household_id)
            if not in_household:
                return ret

            try:
                change = int(data.get("change", "0"))
            except ValueError:
                return {"status": "Change must be an integer"}, 400

            self.app.logger.info(change)
            mapping.amount += change
            self.db.session.commit()
            return {}, 200

        @self.route("/update_product", methods=["POST"])
        @authorize
        def update_product():
            data = dict(request.form)

            username = session.get("username", None)
            self.app.logger.info(username)
            user, ret = get_user_from_db(username)
            if user is None:
                return ret

            mapping_entry = None

            is_product_id = data.pop("is_productid", None)
            if is_product_id is None:
                return {"status": "Field 'is_productid' must be set"}, 400
            is_product_id = string_to_bool(is_product_id)

            product_id = data.pop("id", None)
            if product_id is None:
                return {"status": "Please provide a valid id"}, 400

            if not is_product_id:
                mapping_entry = ProductContainerMapping.query.filter_by(id=product_id).first()
                if mapping_entry is None:
                    return {"status": "Your mapping id could not be found"}, 500
                product_entry = mapping_entry.product
                if product_entry is None:
                    return {"status": "Parent to mapping entry could not be found"}, 500
            else:
                product_entry = Product.query.filter_by(id=product_id).first()
                if product_entry is None:
                    return {"status": "Your product id could not be found"}, 500

            in_household, ret = user_in_household(user.id, product_entry.household_id)
            if not in_household:
                return ret

            starred = data.pop("starred", None)
            if starred is not None:
                starred = string_to_bool(starred)
                product_entry.starred = starred

            name = data.pop("name", None)
            if name is not None:
                product_entry.name = name
            self.app.logger.info(product_entry)
            self.db.session.commit()
            if mapping_entry is None:

                if len(data) != 0:
                    return {"status": "Mapping specific data not updated, due to incorrect id provision"}, 206

                return {}, 200

            box_id = data.pop("box", None)
            location_id = data.pop("location", None)


            if box_id is not None and location_id is not None:
                return {"status": "Please only supply either a location id or a box id"}, 400

            success = False,
            ret = ({}, 200)

            # TODO if the product already exists at the target location stack the amount!

            if box_id is not None:
                success, ret = update_container_id(box_id, ContainerTypes.Box, mapping_entry,
                                                   product_entry.household_id, user.id, self.app.logger)
            elif location_id is not None:
                success, ret = update_container_id(location_id, ContainerTypes.Location, mapping_entry,
                                                   product_entry.household_id, user.id, self.app.logger)

            amount = data.pop("amount", None)
            if amount is not None:
                try:
                    amount = int(amount)
                except ValueError as e:
                    self.app.logger.error(e)
                    return {"status": "amount needs to be an integer"}, 400
                if amount < 0:
                    return {"status": "amount needs to be positive"}, 400

                mapping_entry.amount = amount
                success = True

            if success:
                mapping_entry.updated_at = datetime.datetime.utcnow()
                self.db.session.commit()

            return mapping_entry.serialize(), 200

        @self.route("/delete_product", methods=["DELETE"])
        @authorize
        def delete_product():
            username = session.get("username", None)
            self.app.logger.info(username)
            user, ret = get_user_from_db(username)
            if user is None:
                return ret

            is_product_id = request.args.get("is_productid", None)
            if is_product_id is None:
                return {"status": "Field 'is_productid' must be set"}, 400
            is_product_id = string_to_bool(is_product_id)

            product_id = request.args.get("id", None)
            if product_id is None:
                return {"status": "Please provide a valid id"}, 400

            if is_product_id:
                entry = Product.query.filter_by(id=product_id).first()
                if entry is None:
                    return {"status": "Nothing to delete"}, 400
                in_household, ret = user_in_household(user.id, entry.household_id)
                if not in_household:
                    return ret
                self.app.logger.info("DELETING WHOLE PRODUCT")
            else:
                entry = ProductContainerMapping.query.filter_by(id=product_id).first()
                if entry is None:
                    return {"status": "Nothing to delete"}, 400
                in_household, ret = user_in_household(user.id, entry.product.household_id)
                if not in_household:
                    return ret
                self.app.logger.info("DELETING PRODUCT AT LOCATION/IN BOX")
            self.db.session.delete(entry)
            self.db.session.commit()
            return {}, 200

        @self.route("/add_product", methods=["POST"])
        @authorize
        def add_product():

            data = dict(request.form)
            username = session.get("username", None)
            self.app.logger.info(username)
            user, ret = get_user_from_db(username)
            if user is None:
                return ret

            product = Product.query.filter_by(id=data.pop("product", None)).first()
            if product is None:
                return {"status": "Please specify a valid product"}, 400

            in_household, ret = user_in_household(user.id, product.household_id)
            if not in_household:
                return ret
            amount = data.pop("amount", None)
            try:
                amount = int(amount)
            except ValueError as e:
                self.app.logger.error(e)
                return {"status": "amount needs to be a valid integer"}, 400

            box_id = data.pop("box", None)
            location_id = data.pop("location", None)

            if box_id is not None and location_id is not None:
                self.app.logger.warn("Trying to set location and box at the same time")
                return {"status": "Only a box or a location can be set"}, 400

            if box_id is not None:
                try:
                    box_id = int(box_id)
                except ValueError as e:
                    self.app.logger.error(e)
                    return {"status": "invalid box id"}, 400

                box = Box.query.filter_by(id=box_id).first()
                in_household, ret = user_in_household(user.id, box.household_id)
                if not in_household:
                    return ret

                mapping = [mapping for mapping in product.mappings if mapping.product_id == product.id and
                           mapping.box_id == box_id and mapping.location_id is location_id]
            elif location_id is not None:
                try:
                    location_id = int(location_id)
                except ValueError as e:
                    self.app.logger.error(e)
                    return {"status": "invalid box id"}, 400
                location = Location.query.filter_by(id=location_id).first()
                in_household, ret = user_in_household(user.id, location.household_id)
                if not in_household:
                    return ret
                mapping = [mapping for mapping in product.mappings if mapping.product_id == product.id and
                           mapping.box_id is box_id and mapping.location_id == location_id]
            else:
                mapping = [mapping for mapping in product.mappings if mapping.product_id == product.id and
                           mapping.box_id is box_id and mapping.location_id is location_id]

            if len(mapping) == 0:
                mapping = ProductContainerMapping(product_id=product.id, amount=amount,
                                                  box_id=box_id, location_id=location_id)
                self.db.session.add(mapping)

            else:
                mapping = mapping[0]
                mapping.amount += amount
            self.db.session.commit()
            self.app.logger.info(mapping)

            return {}, 200



