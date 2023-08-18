from models.StorageContainer import Box, Location, ContainerTypes
from models.User import User, HouseholdMembers


def user_in_household(user_id, household_id):
    household_member = HouseholdMembers.query.filter_by(member_id=user_id, household_id=household_id).first()
    if household_member is None:
        return False, ({"status": "Operation not possible because not everything is associated to the users household"}, 400)
    return True, None


def get_user_from_db(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return None, ({"status": "User not found. Try again later"}, 500)
    return user, None


def string_to_bool(to_convert):
    return to_convert in ["yes", "y", "1", "true", "True"]


def in_same_household(product_household, container_household):
    if product_household != container_household:
        return False, ({"status": "Product and storage container need to be in the same household"}, 400)
    return True, None


def update_container_id(container_id, container_type: ContainerTypes, entry, product_household, user_id, logger=None):
    if container_type != ContainerTypes.Box and  container_type != ContainerTypes.Location:
        return False, None

    if container_id is not None:
        try:
            container_id = int(container_id)
        except ValueError as e:
            if logger is not None:
                logger.error(e)
            return False, ({"status": f"{container_type} should be an integer"}, 500)

        if container_id == -1:
            container_id = None
        else:
            if container_type == ContainerTypes.Box:
                box = Box.query.filter_by(id=container_id).first()
                if box is None:
                    return False, ({"status": "No valid box given"}, 400)
                container_household = box.household_id
            elif container_type == ContainerTypes.Location:
                location = Location.query.filter_by(id=container_id).first()
                if location is None:
                    return False, ({"status": "No valid location given"}, 400)
                container_household = location.household_id
            else:
                container_household = -1
            in_household, ret = user_in_household(user_id, container_household)
            if not in_household:
                return False, ret

            same_household, ret = in_same_household(product_household, container_household)
            if not same_household:
                return False, ret

        updated = False

        if container_type == ContainerTypes.Box and entry.box_id != container_id:
            logger.info(f"Moving product '{entry.id}' from box '{entry.box_id}' to box '{container_id}'")
            entry.box_id = container_id
            entry.location_id = None
            updated = True

        elif container_type == ContainerTypes.Location and entry.location_id != container_id:
            logger.info(f"Moving product '{entry.id}' from loc '{entry.location_id}' to loc '{container_id}'")
            entry.location_id = container_id
            entry.box_id = None
            updated = True
        return updated, ({"status": ""}, 200)


def container_name_unique(household_id, container_id, container_type: ContainerTypes, name):
    if container_type == ContainerTypes.Box:
        container = Box.query.filter_by(household_id=household_id, name=name).first()
    elif container_type == ContainerTypes.Location:
        container = Location.query.filter_by(household_id=household_id, name=name).first()
    else:
        return True
    return container is None or container_id == container.id
