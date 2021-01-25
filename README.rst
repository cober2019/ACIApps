.. image:: https://travis-ci.com/cober2019/ACIApps.svg?token=Jd38SqdR7ErpxMoqVxEQ&branch=main
    :target: https://travis-ci.com/cober2019/ACIApps
.. image:: https://img.shields.io/badge/APIC--4.1-passing-green
    :target: -
    

ACI Apps
=========

Usage
______

    - Run requirements.txt to install requred python modules: pip3 install -r requirements.txt
    - Launch the App using run.py in the main folder. To access the app use http://127.0.0.1:5000/
    - **Don't have ACI? Visit Cisco Devent Sandbox and take it for a test drive.**

Description:
____________

ACI apps is an easy to use set of tools for Cisco ACI. The following modules are included in this app are:
 
    **- Encap Finder**
    
        **Finds L2 encapsulation and all fabric policies assigned to them. It will also show you where the encap is locationed in your fabric.**
        
        .. image:: https://github.com/cober2019/ACIApps/blob/main/images/encapFinder.PNG
       
    **- Endpoint Finder**
    
        **Finds an endpoint within your fabric and gives the location. It will also provide a reverse look for the endpoint as well.**
        
       .. image:: https://github.com/cober2019/ACIApps/blob/main/images/ENDPOINTfINDER.PNG
    
       .. image:: https://github.com/cober2019/ACIApps/blob/main/images/GUI_EP_Lookup.PNG
        
    **- Subnet Finder**
    
        **Find where a subnet/unicast gateway is located in your fabric and displays the information.**
        
      .. image:: https://github.com/cober2019/ACIApps/blob/main/images/GatewayFinder.PNG
        
    **- Infrastructure Info**
    
       **Shows your pod information along with node IDs, health statuses, and serial numbers.**
       
      .. image:: https://github.com/cober2019/ACIApps/blob/main/images/infra.PNG
       
