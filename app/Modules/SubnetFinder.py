"""Helper program for locating subnets in ACI"""


import xml.etree.ElementTree as ET
import warnings

# Check and ignore unverfied http reequest
warnings.filterwarnings('ignore', message='Unverified HTTPS request')


def request_subnets(session, apic):
    """Request ACI subnets, checks response for vailidity"""

    root = None
    uri = f"https://{apic}/api/class/fvBD.xml?query-target=subtree"
    response = session.get(uri, verify=False)

    try:
        root = ET.fromstring(response.text)
    except ET.ParseError:
        print("Something went wrong. Please try again")

    return root


def get_subnets(session, apic):
    """Gets current gateways in ACI"""

    root = request_subnets(session, apic)
    unicast = []
    for gateway in root.iter("fvSubnet"):
        subnets = gateway.get("ip")
        unicast.append(subnets)

    return root


def get_gateways(session, apic):

    gateways = []

    get_gateway = get_subnets(session, apic)
    for fvSubnet in get_gateway.iter("fvSubnet"):
        ip = fvSubnet.get("ip")
        gateways.append(ip)

    return gateways

def find_gateways(unicast_gateway, session, apic) -> tuple:
    """Search for ACI Gateways and get configurations"""

    get_gateway = get_subnets(session, apic)

    aps = []
    epgs = []
    l3Outs = []
    gateways = []

    location, bridge_domain, uni_route, scope, unkwn_uni, tenant, bd_vrf, iplearn = None, "DoesntExist", None, None, None, None, None, None

    try:
        # Locate subnet in ACI, get scope, map location
        for fvSubnet in get_gateway.iter("fvSubnet"):
            ip = fvSubnet.get("ip")
            gateways.append(ip)
            if unicast_gateway in ip:
                location = fvSubnet.get("dn")
                scope = fvSubnet.get("scope")
                break

        # Find BD, check to see if unicast routing is enable and unknown unicast setting is
        for fvBD in get_gateway.iter("fvBD"):
            bds = fvBD.get("name")
            iplearn = fvBD.get("ipLearning")
            mtu = fvBD.get("mtu")
            learn_limit = fvBD.get("limitIpLearnToSubnets")
            mac = fvBD.get("mac")
            if location.rfind(bds) != -1:
                bridge_domain = bds
                uni_route = fvBD.get("unicastRoute")
                unkwn_uni = fvBD.get("unkMacUcastAct")

        # Find vrf associated with BD
        for fvRsCtx in get_gateway.iter("fvRsCtx"):
            vrf = fvRsCtx.get("tnFvCtxName")
            location = fvRsCtx.get("dn")
            if location.rfind(bridge_domain) != -1:
                bd_vrf = vrf

        # Find tenant, ap, and epgs, save to list
        for fvRtBd in get_gateway.iter("fvRtBd"):
            dn = fvRtBd.get("dn")
            if dn.rfind(bridge_domain) != -1:
                tenant = dn.split("/")[1].strip("tn-")
                aps.append(dn.split("/")[5].strip("ap-"))
                epgs.append(dn.split("/")[6].strip("epg-").strip("]"))

        # Find L3outs, save to list
        for fvRsBDToOut in get_gateway.iter("fvRsBDToOut"):
            dn = fvRsBDToOut.get("dn")
            if dn.rfind(bridge_domain) != -1:
                l3Outs.append(dn.split("/")[3].strip("rsBDToOut-"))

        # Find L3outs, save to list
        for ipLearning in get_gateway.iter("ipLearning"):
            iplearn = ipLearning.get("ipLearning")


    except AttributeError:
        pass

    # Set variables from conditions
    if aps:
        join_aps = ', '.join(aps)
    else:
        join_aps = None

    if epgs:
        join_epgs = ', '.join(epgs)
    else:
        join_epgs = None

    if l3Outs:
        join_l3outs = ', '.join(l3Outs)
    else:
        join_l3outs = None

    if not bd_vrf:
        bd_vrf = None

    if not unicast_gateway:
        bridge_domain = 0

    # Return to user input
    return bridge_domain, uni_route, scope, unkwn_uni, tenant, join_aps, join_epgs, join_l3outs, bd_vrf, iplearn, mtu, learn_limit, mac, gateways

