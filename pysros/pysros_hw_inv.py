from pysros.management import connect
from pysros.exceptions import *
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader
import sys, yaml, json

def get_connection(router, 
                   username, 
                   password, 
                   port=830, 
                   hostkey_verify=False):
    try:
        c = connect(host=router,
                    username=username,
                    password=password,
                    port=port,
                    hostkey_verify = hostkey_verify)
    except RuntimeError as e1:
        print("Failed to connect.  Error:", e1)
        sys.exit(-1)
    except ModelProcessingError as e2:
        print("Failed to create model-driven schema.  Error:", e2)
        sys.exit(-2)
    return c

    
def get_json(conn_obj, path):
    # converts the native pysros data structure
    # to a json dict for easier parsing
    payload = conn_obj.running.get(path)
    return json.loads(conn_obj.convert(path=path, 
                                       payload=payload, 
                                       source_format='pysros', 
                                       destination_format='json', 
                                       pretty_print=True))
    

def check_flash(conn_obj):
    # keys are flash-id (cf<flash-id>:)
    # we also want capacity, free-space, and percent-used
    path = '/nokia-state:state/cpm[cpm-slot="A"]/flash[flash-id=3]'
    fd = get_json(conn_obj, path)
    d = defaultdict()
    d['flash'] = fd
    return d
    

def check_mda(conn_obj):
    # keys are mda-slot number
    # we also want equipped-type and equipped-ports from each slot
    path = '/nokia-state:state/card[slot-number=1]/mda'
    md = get_json(conn_obj, path)
    d = defaultdict()
    d['mda'] = md
    return d


def check_chassis(conn_obj):
    # 
    path = '/nokia-state:state/chassis'
    cd = get_json(conn_obj, path)
    d = defaultdict()
    d['chassis'] = cd
    return d


def merge_dicts(list_of_dicts):
    super_dict = defaultdict()
    for d in list_of_dicts:
        super_dict.update(d)
    return super_dict
            
            
def render_output(vars):
    environment = Environment(loader=FileSystemLoader("templates/"))
    template = environment.get_template("pysros_hw_inv.j2")
    print(template.render(vars=vars))

          
def main():
    with open('router_info.yml', 'r') as fh:
        router_info = yaml.load(fh, Loader=yaml.SafeLoader)
    routers = router_info['routers']['sros']
    username = router_info['username']
    password = router_info['password']
    port = router_info['port']
    hostkey_verify = router_info['hostkey_verify']
    for router in routers:
        c = get_connection(router, username, password, port, hostkey_verify)
        router = router.split('-')[3]
        flash = check_flash(c)
        mda_card = check_mda(c)
        chassis = check_chassis(c)
        c.disconnect()
        router_name = { 'router_name' : router }
        vars = merge_dicts([ router_name, flash, mda_card, chassis ])
        render_output(vars)


if __name__ == "__main__":
    main()