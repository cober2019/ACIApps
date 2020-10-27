import time
from app.Modules.FindEncap import apic_login
import app.base.routes as Routes


def session_time(username, password, apic):
    session_time = time.perf_counter()

    if session_time > 1100:
        apic_session = apic_login(username, password, apic)
        Routes.apic_session = apic_session
