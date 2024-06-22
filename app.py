import logging
from flask import Flask, request, render_template, jsonify
from flask_restx import Api, Resource, fields
import dns.resolver
import dns.query
import dns.message
import requests
import json
import socket

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Uncomment the following line to disable all app logging
# logging.getLogger().addHandler(logging.NullHandler())

# Suppress Flask's server startup messages
#log = logging.getLogger('werkzeug')
#log.setLevel(logging.ERROR)

# Suppress urllib3 debug messages
#logging.getLogger('urllib3').setLevel(logging.WARNING)

app = Flask(__name__)
api = Api(app, version='1.0', title='DNS Lookup API',
          description='A simple DNS Lookup API. Visit /dns-lookup for the DNS lookup form.',
          prefix='/api',
          doc='/api'  # Serve Swagger UI at /api
          )

ns = api.namespace('dns', description='DNS operations')

# Add the namespace to the API
api.add_namespace(ns, path='/dns')

# Load configuration from file
with open('config.json') as config_file:
    config = json.load(config_file)

# Define the allowed DNS query types as an enumeration
dns_query_types = [
    'A', 'AAAA', 'CAA', 'CNAME', 'MX', 'NS', 'PTR', 'SOA',
    'SRV', 'TXT', 'DS', 'DNSKEY', 'NSEC', 'NSEC3', 'RRSIG',
    'TLSA', 'SMIMEA', 'SPF', 'SSHFP'
]

# Define the expected model for the API input
dns_lookup_model = api.model('DNSLookup', {
    'dns_name': fields.String(required=True, description='The DNS name to lookup'),
    'dns_type': fields.String(required=False, description='The DNS query type', enum=dns_query_types),
    'dns_servers': fields.List(fields.String, description='List of DNS servers to query', default=['8.8.8.8', '1.1.1.1']),
    'protocol': fields.String(required=False, description='The DNS protocol to use', enum=['UDP', 'TCP', 'DoH', 'DoT'], default='UDP')
})

def log_debug(message):
    if app.config['DEBUG']:
        logger.debug(message)

def doh_lookup(dns_name, dns_type, dns_server):
    log_debug(f"Performing DoH lookup for {dns_name} using {dns_server}")
    doh_url = f'https://{dns_server}/dns-query'
    headers = {'accept': 'application/dns-json'}
    params = {'name': dns_name, 'type': dns_type}
    response = requests.get(doh_url, headers=headers, params=params, timeout=3)
    if response.status_code == 200:
        data = response.json()
        log_debug(f"DoH response data: {data}")
        answers = []
        for item in data.get('Answer', []):
            record_type = dns.rdatatype.to_text(item['type'])
            answers.append({
                "query_name": item['name'],
                "record": item['data'],
                "type": record_type,
                "ttl": item['TTL'],
                "authoritative": False
            })
        return answers
    else:
        log_debug(f"DoH request failed with status code {response.status_code}")
        raise Exception(f"DoH request failed with status code {response.status_code}")

def dot_lookup(dns_name, dns_type, dns_server):
    log_debug(f"Performing DoT lookup for {dns_name} using {dns_server}")
    query = dns.message.make_query(dns_name, dns_type)
    response = dns.query.tls(query, dns_server, timeout=3)
    log_debug(f"DoT response: {response}")
    answers = []
    for rrset in response.answer:
        record_type = dns.rdatatype.to_text(rrset.rdtype)
        for rdata in rrset:
            answers.append({
                "query_name": rrset.name.to_text(),
                "record": rdata.to_text(),
                "type": record_type,
                "ttl": rrset.ttl,
                "authoritative": response.flags & dns.flags.AA != 0
            })
    return answers

def direct_dns_lookup(dns_name, dns_type, dns_server_ip, protocol):
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [dns_server_ip]
    resolver.timeout = 3
    resolver.lifetime = 3
    if protocol == 'TCP':
        resolver.use_tcp = True
    response = resolver.resolve(dns_name, dns_type)
    log_debug(f"Direct DNS response: {response.response}")
    answers = []
    for rrset in response.response.answer:
        record_type = dns.rdatatype.to_text(rrset.rdtype)
        for rdata in rrset:
            answers.append({
                "query_name": rrset.name.to_text(),
                "record": rdata.to_text(),
                "type": record_type,
                "ttl": rrset.ttl,
                "authoritative": response.response.flags & dns.flags.AA != 0
            })
    return answers

def api_lookup(dns_name, dns_type, dns_server, protocol, url):
    payload = {
        'dns_name': dns_name,
        'dns_type': dns_type,
        'dns_servers': [dns_server],
        'protocol': protocol
    }
    log_debug(f"API Call URL: {url}")
    log_debug(f"API Call Payload: {json.dumps(payload, indent=2)}")

    response = requests.post(url, json=payload, timeout=10)
    if response.status_code == 200:
        data = response.json()
        results = []
        for answer in data.get('results', {}).get(dns_server, []):
            results.append({
                "query_name": answer.get('name'),
                "record": answer.get('data'),
                "type": dns.rdatatype.to_text(answer.get('type')),
                "ttl": answer.get('TTL'),
                "authoritative": False
            })
        return results
    else:
        raise Exception(f"API request failed with status code {response.status_code}")

def is_local_url(url):
    parsed_url = url.split('/')
    if len(parsed_url) > 2:
        hostname = parsed_url[2].split(':')[0]
        local_ips = [ip[4][0] for ip in socket.getaddrinfo(socket.gethostname(), None)]
        local_ips.append('127.0.0.1')
        try:
            remote_ip = socket.gethostbyname(hostname)
            return remote_ip in local_ips
        except socket.error:
            return False
    return False

def perform_dns_lookup(dns_name, dns_type, server_config):
    dns_server_ip = server_config['server']
    friendly_name = server_config.get('name', dns_server_ip)
    protocol = server_config.get('protocol', 'UDP')
    url = server_config.get('url')
    server_results = {
        "server": dns_server_ip,
        "friendly_name": friendly_name,
        "results": []
    }

    try:
        if url and is_local_url(url):
            log_debug(f"Performing local DNS lookup for {dns_name} using {dns_server_ip} and protocol {protocol}")
            if protocol == 'DoH':
                server_results["results"] = doh_lookup(dns_name, dns_type, dns_server_ip)
            elif protocol == 'DoT':
                server_results["results"] = dot_lookup(dns_name, dns_type, dns_server_ip)
            else:
                server_results["results"] = direct_dns_lookup(dns_name, dns_type, dns_server_ip, protocol)
        elif url:
            server_results["results"] = api_lookup(dns_name, dns_type, dns_server_ip, protocol, url)
        else:
            log_debug(f"Performing direct DNS lookup for {dns_name} using {dns_server_ip} and protocol {protocol}")
            if protocol == 'DoH':
                server_results["results"] = doh_lookup(dns_name, dns_type, dns_server_ip)
            elif protocol == 'DoT':
                server_results["results"] = dot_lookup(dns_name, dns_type, dns_server_ip)
            else:
                server_results["results"] = direct_dns_lookup(dns_name, dns_type, dns_server_ip, protocol)
    except dns.resolver.NoNameservers:
        server_results["results"].append(f"No response from DNS server: {dns_server_ip}")
    except Exception as e:
        server_results["results"].append(str(e))

    return server_results

@ns.route('/lookup')
class DNSLookup(Resource):
    @ns.expect(dns_lookup_model)
    @ns.response(200, 'Success')
    @ns.response(400, 'Validation Error')
    def post(self):
        """Perform a DNS lookup"""
        data = api.payload
        dns_name = data['dns_name']
        dns_type = data.get('dns_type', 'A') or 'A'  # Default to 'A' if not provided or empty
        results = [perform_dns_lookup(dns_name, dns_type, server_config) for server_config in config['dns_servers']]

        response = {
            'dns_name': dns_name,
            'dns_type': dns_type,
            'results': results
        }
        return jsonify(response)

# Route to handle DNS lookup form and results
@app.route('/dns-lookup', methods=['GET', 'POST'])
def dns_lookup():
    if request.method == 'POST':
        dns_name = request.form['dns_name']
        dns_type = request.form.get('dns_type', 'A') or 'A'  # Default to 'A' if not provided or empty
        advanced = 'advanced' in request.form
        fun_style = 'fun_style' in request.form
        selected_servers = request.form.getlist('dns_servers')
        custom_dns = request.form.get('custom_dns')

        # Add the custom DNS server to the selected servers if provided
        if custom_dns:
            selected_servers.append(custom_dns)

        # Filter the DNS servers based on the selection
        filtered_servers = [server for server in config['dns_servers'] if server['server'] in selected_servers]
        # Add custom DNS server configuration if provided
        if custom_dns:
            filtered_servers.append({
                "server": custom_dns,
                "protocol": "UDP",  # Default protocol for custom DNS server
                "url": "",
                "name": "Custom DNS"
            })
        
        results = [perform_dns_lookup(dns_name, dns_type, server_config) for server_config in filtered_servers]
    
        return render_template('dns_results.html', dns_name=dns_name, dns_type=dns_type, results=results, advanced=advanced, custom_dns=custom_dns, fun_style=fun_style)
    return render_template('dns_form.html', dns_query_types=dns_query_types, dns_servers=config['dns_servers'])

# Custom root route
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
    # app.run(host='0.0.0.0', port=8080, debug=True)
