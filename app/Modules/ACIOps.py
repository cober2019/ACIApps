import json
import xml.etree.ElementTree as ET
import collections


def infr(session, apic):
    """Takes in pod number , and return all information about the fabric hardware. Greate for TAC use"""

    infra_info = collections.defaultdict(list)

    for i in range(1, 10):
        uri = f"https://{apic}/api/node/mo/topology/pod-{i}.xml?query-target=children"

        request = session.get(uri, verify=False)
        if request.text.rfind("totalCount=\"0\"") != -1:
            continue
        else:
            root = ET.fromstring(request.text)

            for fabricNode in root.iter("fabricNode"):
                fabric_node = fabricNode.get("name")
                model_node = fabricNode.get("model")
                serial_node = fabricNode.get("serial")
                infra_info[f"pod{i}"].append({'node': fabric_node, 'model': model_node, 'serial': serial_node})
            for fabricHealthTotal in root.iter("fabricHealthTotal"):
                fabric_prev = fabricHealthTotal.get("prev")
                fabric_change = fabricHealthTotal.get("chng")
                fabric_health = fabricHealthTotal.get("cur")

            infra_info[f"pod{i}"].append({'uri': uri, 'health': int(fabric_health), 'prehealth': int(fabric_prev), 'change': int(fabric_change)})

    return infra_info


class AciOps:

    """Collects authentication information from user, returns session if successfull, or response if not"""

    def __init__(self):

        self.session = None
        self.response = None
        self.apic = None
        self.vlan_dict = collections.defaultdict(list)
        self.policies_dict = collections.defaultdict(list)
        self.device_info = []
        self.tenant_array = []
        self.bd_array = []
        self.ap_array = []
        self.epg_array = []
        self.vrf_array = []
        self.json_header = headers = {'content-type': 'application/json'}

    def view_tenants(self):

        """Returns ACI Tenant from the arbitrary APIC"""

        uri = "https://{}/api/class/fvTenant.json".format(self.apic)

        request = self.session.get(uri, verify=False)
        response_dict = request.json()
        total_count = int(response_dict["totalCount"])

        try:
            index = 0
            self.tenant_array.clear()
            for i in range(0, total_count):
                self.tenant_array.append(response_dict["imdata"][index]["fvTenant"]["attributes"]["name"])
                index = index + 1
        except IndexError:
            pass

        return self.tenant_array

    def view_tenant_vrf(self, tenant=None):

        """View Tenant vrf, return Tenant vrf names"""

        uri = "https://{}/api/node/mo/uni/tn-{}.json?query-target=children&target-subtree-class=fvCtx"\
                                                                            .format(self.apic, tenant)
        request = self.session.get(uri, verify=False)
        response = json.loads(request.text)

        try:
            index = 0
            self.vrf_array.clear()
            for i in range(0, 100):
                self.vrf_array.append(response["imdata"][index]["fvCtx"]["attributes"]["name"])
                index = index + 1
        except IndexError:
            pass

        return self.vrf_array

    def view_bd(self, tenant=None):

        """View Bridge domains of a Tenant, returns bridge domain names"""

        uri = "https://{}/api/node/mo/uni/tn-{}.json?query-target=children&target-subtree-class=fvBD"\
                                                                            .format(self.apic, tenant)
        request = self.session.get(uri, verify=False)
        response = json.loads(request.text)
        total_count = int(response["totalCount"])

        index = 0
        self.bd_array.clear()
        for i in range(0, total_count):
            self.bd_array.append(response["imdata"][index]["fvBD"]["attributes"]["name"])
            index = index + 1

        return self.bd_array

    def view_app_profiles(self, tenant=None):

        """View Application profiles of a particular Tenant, return App profiles"""

        uri = "https://{}/api/node/mo/uni/tn-{}.json?query-target=children&target-subtree-class=fvAp"\
                                                                            .format(self.apic, tenant)
        request = self.session.get(uri, verify=False)
        response = json.loads(request.text)
        total_count = int(response["totalCount"])

        index = 0
        self.ap_array.clear()
        for i in range(0, total_count):
            self.ap_array.append(response["imdata"][index]["fvAp"]["attributes"]["name"])
            index = index + 1

        return self.ap_array

    def view_epgs(self, tenant=None, app=None):

        """View endpoint groups of a particular Tenant-App profile, returns EPG names"""

        uri = "https://{}/api/node/mo/uni/tn-{}/ap-{}.json?query-target=children&target-subtree-class=fvAEPg"\
                                                                                .format(self.apic, tenant, app)
        request = self.session.get(uri, verify=False)
        response = json.loads(request.text)
        total_count = int(response["totalCount"])

        index = 0
        self.epg_array.clear()
        for i in range(0, total_count):
            self.epg_array.append(response["imdata"][index]["fvAEPg"]["attributes"]["name"])
            index = index + 1

        return self.epg_array


class AciOpsSend(AciOps):

    """ACI send basic configs. Return value will be APIC response in dictionary structure, or string notify the caller of
    and error"""

    def __init__(self, **kwargs):

        """ Import * from AciOps class. Use AciOps login method to create a http session. Once session has been
        intiated, call AciOps view_tenants method. The AciOps self.session and self.tenant_array will be used
        throughout"""

        super().__init__()
        self.login(apic=kwargs["apic"], username=kwargs["username"], password=kwargs["password"])
        self.view_tenants()

    def create_tenant(self, tenant=None):

        """Create tenant, arg supplied will be tenants name. Conditional check will be done o insure  no duplicates"""

        uri = """https://{}/api/mo/uni.json""".format(self.apic)

        if tenant not in self.tenant_array:

            tenants = """{"fvTenant" : { "attributes" : { "name" : "%s"}}}""" % tenant
            request = self.session.post(uri, verify=False, data=tenants, headers=self.json_header)
            tenants = self.view_tenants()

            return request, tenants
        else:
            return "Tenant: %s Exist" % tenant

    def create_app_profile(self, tenant=None, app=None):

        """Create app prof, args supplied will be tenant, and app prof name.
        Conditional check will be done to insure  no duplicates"""

        app_profiles = self.view_app_profiles(tenant=tenant)

        if app not in app_profiles:
            uri = "https://" + self.apic + "/api/mo/uni/tn-" + tenant + ".json"
            app_profile = "{\"fvAp\": " \
                          "{\"attributes\": " \
                          "{\"name\": \"%s\"}}}}" % app

            request = self.session.post(uri, verify=False, data=app_profile, headers=self.json_header)
            app_profiles = self.view_app_profiles(tenant=tenant)

            return request, app_profiles
        else:
            return "App Profile: %s Exist " % app

    def create_epg(self, tenant=None, app=None, epg=None):

        """Create epg, args supplied will be tenant, and app prof name, and epg name
        Conditional check will be done to insure  no duplicates"""

        epgs = self.view_epgs(tenant=tenant, app=app)

        if epg not in epgs:
            uri = "https://" + self.apic + "/api/mo/uni/tn-" + tenant + "/ap-" + app + ".json"
            epg = "{\"fvAEPg\":" \
                  "{\"attributes\": " \
                  "{\"name\": \"%s\"}}}}" % epg

            request = self.session.post(uri, verify=False, data=epg, headers=self.json_header)
            epgs = self.view_epgs(tenant=tenant, app=app)

            return request, epgs
        else:
            return "EPG: %s Exist" % epg

    def create_bd_l3(self, tenant=None, bd=None, subnet=None, scope=None):

        """Create bd, args supplied will be tenant. Conditional check will be done to insure  no duplicates"""

        bds = self.view_bd(tenant=tenant)

        if bd not in bds:
            uri = "https://" + self.apic + "/api/mo/uni/tn-" + tenant + ".json"
            bridge_dom = "{\"fvBD\":" \
                         "{\"attributes\": " \
                         "{\"name\": \"%s\"" % bd + "}," \
                         "\"children:[" \
                         "{\"fvSubnet\": " \
                         "{\"attributes\":" \
                         "{\"ip\": \"%s\"" % subnet + "," \
                         "{\"scope\": \"%s\"" % scope + "}}}}]}}}"

            request = self.session.post(uri, verify=False, data=bridge_dom, headers=self.json_header)
            bds = self.view_bd(tenant=tenant)
            bd_info = self.subnet_finder(subnet=subnet)

            return request, bds, bd_info

        else:
            return "BD: %s Exist" % bd

    def routing_scope(self, tenant=None, bd=None, subnet=None, scope=None):

        """Configuring routing scope (shared, private, external). First we split the scope to check for validity
        if valid, use the orignal scope arg for the variable"""

        split_scope = scope.split(",")
        scope_list = ["private", "public", "shared"]
        bds = self.view_bd(tenant=tenant)

        for scope in split_scope:
            if scope not in scope_list:
                raise ValueError("Invalid Scope \"{}\" - Expecting private|public|shared".format(scope))
            else:
                pass

        if bd in bds:
            uri = "https://" + self.apic + "/api/mo/uni/tn-" + tenant + "/BD-" + bd + "/subnet-[" + subnet + "].json"
            bridge_dom = "{\"fvSubnet\": " \
                         "{\"attributes\":" \
                         "{\"scope\": \"%s\"" % scope + "}}}"

            request = self.session.post(uri, verify=False, data=bridge_dom, headers=self.json_header)
            bds = self.view_bd(tenant=tenant)
            bd_info = self.subnet_finder(subnet=subnet)

            return request, bds, bd_info

        else:
            return "BD: %s Exist" % bd

    def enable_unicast(self, tenant=None, bd=None, enable=None):

        """Create bd, args supplied will be tenant  Conditional check will be done to insure  no duplicates,
        require yes/no input"""

        bds = self.view_bd(tenant=tenant)
        yes_no = ["yes", "no"]

        if enable not in yes_no:
            raise ValueError("Invalid arg \"{}\" - Expecting yes/no".format(enable))
        if bd in bds:
            uri = "https://" + self.apic + "/api/mo/uni/tn-" + tenant + ".json"
            bridge_dom = "{\"fvBD\":" \
                         "{\"attributes\": " \
                         "{\"name\": \"%s\"" % bd + ", \"" \
                         "unicastRoute\": \"%s\"" % enable + "}}}"

            request = self.session.post(uri, verify=False, data=bridge_dom, headers=self.json_header)

            return request, bridge_dom

        else:
            return "BD: %s Exist" % bd

    def create_bd_l2(self, tenant=None, bd=None):

        """Create L2 bd, args supplied will be tenant  Conditional check will be done to insure  no duplicates"""

        bds = self.view_bd(tenant=tenant)

        if bd not in bds:

            uri = "https://" + self.apic + "/api/mo/uni/tn-" + tenant + ".json"
            bridge_dom = "{\"fvBD\":" \
                         "{\"attributes\": " \
                         "{\"name\": \"%s\"" % bd + "}}}"

            request = self.session.post(uri, verify=False, data=bridge_dom, headers=self.json_header)
            bds = self.view_bd(tenant=tenant)

            return request, bds
        else:
            return "BD: %s Exist" % bd

    def create_vrf(self, tenant=None, vrf=None):

        """Create tenant vrf, args supplied will be tenant  Conditional check will be done to insure  no duplicates"""

        vrfs = self.view_tenant_vrf(tenant=tenant)

        if vrf not in vrfs:
            uri = "https://" + self.apic + "/api/mo/uni/tn-" + tenant + ".json"
            vrf = "{\"fvCtx\":" \
                  "{\"attributes\": " \
                  "{\"name\": \"%s\"" % vrf + "}}}"

            request = self.session.post(uri, verify=False, data=vrf, headers=self.json_header)
            vrfs = self.view_tenant_vrf(tenant=tenant)

            return request, vrfs
        else:
            return "Vrf: %s Exist" % vrf

    def vrf_to_bd(self, tenant=None, bd=None, vrf=None):

        """Assign vrf to bd, args supplied will be tenant, bd name, vrf name
        Conditional check will be done to insure vrf has been configured"""

        vrfs = self.view_tenant_vrf(tenant=tenant)

        if vrf in vrfs:
            uri = "https://" + self.apic + "/api/mo/uni/tn-" + tenant + ".json"
            vrf_bd = "{\"fvBD\":" \
                     "{\"attributes\": " \
                     "{\"name\": \"%s\"" % bd + "}," \
                     "\"children:[" \
                     "{\"fvRsCtx \": " \
                     "{\"attributes\":" \
                     "{\"tnFvCtxName\": \"%s\"" % vrf + "}}}]}}}"

            request = self.session.post(uri, verify=False, data=vrf_bd, headers=self.json_header)
            vrfs = self.view_tenant_vrf(tenant=tenant)

            return request, vrfs
        else:
            return "VRF: %s Doesn't Exist " % vrf


