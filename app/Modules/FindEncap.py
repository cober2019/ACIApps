"""Helper funtions to get information about ACI encapsulations"""

import app.Modules.ACI_Policies as GetPolicies
import requests
import warnings


def apic_login(username, password, apic) -> object:
    """Login into apic and request access policy configurations"""

    session = None

    uri = f"https://{apic}/api/mo/aaaLogin.xml"
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    raw_data = f"""<!-- AAA LOGIN --> <aaaUser name="{username}" pwd="{password}"/>"""

    # APIC login, failed login or ivalid APIC will result in reprompting credentials.
    try:
        session = requests.Session()
        r = session.post(uri, data=raw_data, verify=False)
        response = r.text
        if response.rfind("FAILED local authentication") != -1 or response.rfind("Failed to parse login request") != -1:
            return None
    except (requests.exceptions.ConnectionError, requests.exceptions.InvalidURL):
        return None

    return session


def encap_selection(encap, session, apic) -> tuple:
    """Gets and prints mapped policies"""

    # Configuration will be return in a tuple, index and joing tuples with newline
    pools = GetPolicies.map_policy_configurations(session, apic, encap)
    print(pools)

    return pools[0], pools[1], pools[2], pools[3], pools[4]




