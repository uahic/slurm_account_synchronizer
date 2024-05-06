def check_valid_declared_groups(unix_group_map: dict, config: dict) -> None:
    if not config["declared_groups"]:
        raise Exception(f"Top-level Key 'declared_groups' are not found")

    def check_group_in_key_exist(grp_entry: dict, key: str) -> None:
        for unix_grp_name in grp_entry[key].keys():
            if not unix_grp_name in unix_group_map:
                raise Exception(
                    f"The group with name '{unix_grp_name}' declared in declared_groups/{grp_name}/{key}/ does not exist on your system."
                )

        for grp_name, grp_entry in config["declared_groups"].items():
            if grp_name in unix_group_map:
                raise Exception(
                    f"Declared (virtual) group name '{grp_name}' collides with a real unix group name."
                )
            if not "groups" in grp_entry or len(grp_entry["groups"]) < 1:
                raise Exception(
                    f"Declared group '{grp_name}' lacks the key 'groups' or has no entries."
                )
            check_group_in_key_exist(grp_entry, "groups")
            check_group_in_key_exist(grp_entry, "whitelist")

            if (
                grp_entry["defaultaccount"]
                and not grp_entry["defaultaccount"] in config["accounts"]
            ):
                raise Exception(
                    f"Defaultaccount specified in declared_groups/{grp_name} is not defined in the accounts section."
                )
