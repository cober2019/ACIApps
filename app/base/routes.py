# -*- encoding: utf-8 -*-

from flask import render_template, redirect, request, url_for, jsonify, flash
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)
from app import login_manager
from app.base import blueprint
from app.base.forms import LoginForm
from app.base.models import User
from app.base.util import verify_pass
import app.Modules.ACI_Policies as GetPolicies
import app.Modules.FindEncap as FindEncap
import app.Modules.EndpointTracker as EpTracker
import app.Modules.SubnetFinder as GetGateway
import app.Modules.ACIOps as AciOps
from app.Modules.GeneralFunctions import session_time
import ipaddress

apic = None
username = None
password = None
apic_session = None


@blueprint.route('/')
def route_default():
    return redirect(url_for('base_blueprint.login'))


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    global apic, username, password, apic_session

    login_form = LoginForm(request.form)
    if 'login' in request.form:

        apic = request.form['apic']
        username = request.form['username']
        password = request.form['password']

        if apic and username and password:

            # Network connection objects
            apic_session = FindEncap.apic_login(username, password, apic)

            if apic_session is not None:

                GetPolicies.vlan_pools(apic_session, apic)
                GetPolicies.domains(apic_session, apic)
                session_time(username, password, apic)
                return redirect(url_for('base_blueprint.find_encap'))
            else:
                flash("Login Failed")
                return render_template('accounts/login.html', form=login_form)

    if not current_user.is_authenticated:
        return render_template('accounts/login.html', form=login_form)
    return redirect(url_for('home_blueprint.index'))


@blueprint.route('/logout')
def logout():
    """User logout"""

    logout_user()
    return redirect(url_for('base_blueprint.login'))


@blueprint.route('/about')
def about():
    """User logout"""

    return render_template('about.html')


@blueprint.route('/submit_encap')
def find_encap():
    """Gets ACI policies"""

    session_time(username, password, apic)

    return render_template('submit_encap.html')


@blueprint.route('/submit_encap', methods=['POST'])
def submit_encap():
    """Find requested encap from user"""

    session_time(username, password, apic)

    encap = request.form.get("encap")
    get_policies = GetPolicies.map_policy_configurations(apic_session, apic, encap)

    return jsonify({'data': render_template('map_policies.html', object_list=get_policies)})


@blueprint.route('/submit_endpoint')
def find_endpoint():

    session_time(username, password, apic)
    return render_template('submit_endpoint.html')


@blueprint.route('/submit_endpoint', methods=['POST'])
def submit_endpoint():

    session_time(username, password, apic)
    endpoint = request.form.get("endpoint")

    try:
        ipaddress.IPv4Address(endpoint)
        get_endpoint = EpTracker.find_ip_endpoints(endpoint, apic_session, apic)
        get_reverse = EpTracker.find_mac_endpoints(get_endpoint[0], apic_session, apic)
    except ipaddress.AddressValueError:
        get_endpoint = EpTracker.find_mac_endpoints(endpoint, apic_session, apic)
        get_reverse = EpTracker.find_ip_endpoints(get_endpoint[0], apic_session, apic)

    return jsonify({'data': render_template('map_endpoint.html', object_list=get_endpoint, reverse=get_reverse)})


@blueprint.route('/submit_subnet')
def find_subnet():

    session_time(username, password, apic)
    return render_template('submit_subnet.html')


@blueprint.route('/submit_subnet', methods=['POST'])
def submit_subnet():

    session_time(username, password, apic)
    gateway = request.form.get("gateway")
    get_gateway = GetGateway.find_gateways(gateway, apic_session, apic)

    return jsonify({'data': render_template('map_subnet.html', object_list=get_gateway)})


@blueprint.route('/infra')
def view_infra():

    session_time(username, password, apic)
    get_infra_info = AciOps.infr(apic_session, apic)

    return render_template('infra.html', fabric_infra=get_infra_info)


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('page-403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden():
    return render_template('page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error():
    return render_template('page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error():
    return render_template('page-500.html'), 500
