"""Helper program/funtions to find endpoint in an ACI Fabric"""


import xml.etree.ElementTree as ET
import warnings
import json

# Ignore HTTP warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')


def get_endpoint_by_mac(endpoint, session, apic) -> tuple:
    """Request endpoing data by mac using json and xml"""

    root = None
    json_to_dict = None
    uri_xml = f"https://{apic}/api/node/class/fvCEp.xml?rsp-subtree=full&rsp-subtree-class=fvCEp,fvRsCEpToPathEp,fvIp," \
              f"fvRsHyper,fvRsToNic,fvRsToVm&query-target-filter=eq(fvCEp.mac,\"{endpoint}\""
    uri_json = f"https://{apic}/api/node/class/fvCEp.json?rsp-subtree=full&rsp-subtree-class=fvCEp,fvRsCEpToPathEp,fvIp," \
               f"fvRsHyper,fvRsToNic,fvRsToVm&query-target-filter=eq(fvCEp.mac,\"{endpoint}\""

    # Makes web request
    xml_reponse = session.get(uri_xml, verify=False)
    json_response = session.get(uri_json, verify=False)

    # Converts xml reponse string to element tree
    try:
        root = ET.fromstring(xml_reponse.text)
    except ET.ParseError:
        pass
    # Converts json response to dictionary
    try:
        json_to_dict = json.loads(json_response.text)
    except json.JSONDecodeError:
        pass

    return root, json_to_dict


def get_endpoint_by_ip(endpoint, session, apic) -> tuple:
    """Request endpoing data by ip using json and xml"""

    root = None
    json_to_dict = None
    uri_xml = f"https://{apic}/api/node/class/fvCEp.xml?rsp-subtree=full&rsp-subtree-include=required&rsp-subtree-filter=" \
              f"eq(fvIp.addr,\"{endpoint}\""
    uri_json = f"https://{apic}/api/node/class/fvCEp.json?rsp-subtree=full&rsp-subtree-include=required&rsp-subtree-filter=" \
               f"eq(fvIp.addr,\"{endpoint}\""

    # Makes web request
    xml_reponse = session.get(uri_xml, verify=False)
    json_response = session.get(uri_json, verify=False)

    # Converts xml reponse string to element tree
    try:
        root = ET.fromstring(xml_reponse.text)
    except ET.ParseError:
        pass
    # Converts json response to dictionary
    try:
        json_to_dict = json.loads(json_response.text)
    except json.JSONDecodeError:
        pass

    return root, json_to_dict


def parse_policy_group(attribute) -> str:
    """Parse json for path attachments/policy groups"""

    complete_path = None
    try:
        paths = attribute.get("rn").split("/")[3].split("[")[1].strip("]")
        group = attribute.get("rn").split("/")[2].strip("protpaths-")
        pod = attribute.get("rn").split("/")[1]
        complete_path = f"{pod}->{group}->{paths}"
    except IndexError:
        pass

    return complete_path


def parse_path_group(attribute) -> str:
    """Parse json for path attributes"""

    paths = None
    try:
        paths = attribute.get("rn").split("/")[2].split("[")[1].strip("]")
    except IndexError:
        pass

    return paths


def find_ip_endpoints(endpoint, session, apic) -> tuple:
    """Collect all data about the requested endpoint if ip"""

    leafs = []
    paths = []
    encap = None
    ep_loc = None
    ep_domain = None
    mac = None

    # Request endpoint data and iterate through elements/atrributes in tree
    root = get_endpoint_by_ip(endpoint, session, apic)
    for fvCEp in root[0].iter("fvCEp"):
        mac = fvCEp.get("mac")
        encap = fvCEp.get("encap")
        ep_loc = fvCEp.get("dn")
        ep_domain = fvCEp.get("lcC")

    try:
        # Using json dictionary, collecting the nodes report the enpoint.
        for node in root[1].get('imdata', {})[0].get('fvCEp', {}).get('children', {})[0].get('fvIp', {}).get('children',
                                                                                                             {}):
            reporting_node = node.get('fvReportingNode', {}).get('attributes', {}).get('id', {})
            leafs.append(reporting_node)
    except (IndexError, KeyError):
        pass

    endpoint_details = display_endpoint_data(ep_loc, encap, ep_domain, mac, paths, leafs)

    return endpoint_details


def find_mac_endpoints(endpoint, session, apic) -> tuple:
    """Collect all data about the requested endpoint if mac"""

    leafs = []
    paths = []
    encap = None
    ep_loc = None
    ep_domain = None
    ip = None

    # Request endpoint data and iterate through elements/atrributes in tree
    root = get_endpoint_by_mac(endpoint, session, apic)
    for fvCEp in root[0].iter("fvCEp"):
        ip = fvCEp.get("ip")
        encap = fvCEp.get("encap")
        ep_loc = fvCEp.get("dn")
        ep_domain = fvCEp.get("lcC")

    # Request endpoint data and iterate through elements/atrributes collecting path data
    for fvRsCEpToPathEp in root[0].iter("fvRsCEpToPathEp"):
        path = parse_path_group(fvRsCEpToPathEp)
        if path is not None:
            paths.append(path)
        path = parse_policy_group(fvRsCEpToPathEp)
        if path is not None:
            paths.append(path)
    try:
        # Using json dictionary, collecting the nodes report the enpoint.
        for node in root[1].get('imdata', {})[0].get('fvCEp', {}).get('children', {})[0].get('fvRsHyper', {}).get(
                'children', {}):
            reporting_node = node.get('fvReportingNode', {}).get('attributes', {}).get('id', {})
            leafs.append(reporting_node)
        for node in root[1].get('imdata', {})[0].get('fvCEp', {}).get('children', {})[0].get('fvRsToVm', {}).get(
                'children', {}):
            reporting_node = node.get('fvReportingNode', {}).get('attributes', {}).get("id", {})
            leafs.append(reporting_node)
        for node in root[1].get('imdata', {})[0].get('fvCEp', {}).get('children', {})[0].get('fvRsCEpToPathEp', {}).get(
                'children', {}):
            reporting_node = node.get('fvReportingNode', {}).get('attributes', {}).get('id', {})
            leafs.append(reporting_node)
    except (IndexError, KeyError):
        pass

    endpoint_details = display_endpoint_data(ep_loc, encap, ep_domain, ip, paths, leafs)

    return endpoint_details


def display_endpoint_data(ep_loc, encap, ep_domain, reverse, paths, leafs):
    """Presents the user with data about the requested endpoint"""

    tenant = None
    ap = None
    epg = None
    switches = None
    path = None

    try:

        tenant = ep_loc.split("/")[1].strip("tn-")
        ap = ep_loc.split("/")[2].strip("ap-")
        epg = ep_loc.split("/")[3].strip("epg-")
        switches = ', '.join(leafs)

        if paths:
            path = ', '.join(paths)
        else:
            paths = "No Path Attachments"
    except AttributeError:
        ep = [0]
        return ep

    return reverse, tenant, ap, epg, ep_domain, encap, path, switches

