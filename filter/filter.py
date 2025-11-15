def is_eligible_single(value, requirement):
    if isinstance(requirement, dict):
        return requirement["min"] <= value and value <= requirement["max"]
    elif isinstance(requirement, list):
        return value in requirement
    else:
        return requirement == value


def is_eligible(values, requirements):
    if isinstance(values, list):
        for value in values:
            if is_eligible_single(value, requirements):
                return True

        return False
    else:
        return is_eligible_single(values, requirements)


def eligibility(company, requirements):
    ineligible = []
    eligible = []
    unspecified = []

    for key in requirements:
        requirement = requirements[key]
        value = company.get(key, None)

        if value is None:
            unspecified.append(key)

        if is_eligible(value, requirement):
            eligible.append(key)
        else:
            ineligible.append(key)

    return {"eligible": eligible, "ineligible": ineligible, "unspecified": unspecified}


def filter(company, funds):
    return [eligibility(company, fund["requirements"]) for fund in funds]
