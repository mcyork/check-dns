from flask import Flask, request, render_template, jsonify
from flask_restx import Api, Resource, fields
import dns.resolver
import dns.query
import dns.message
import requests
import json
import socket

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

def doh_lookup(dns_name, dns_type, dns_server):
    doh_url = f'https://{dns_server}/dns-query'
    headers = {'accept': 'application/dns-json'}
    params = {'name': dns_name, 'type': dns_type}
    response = requests.get(doh_url, headers=headers, params=params, timeout=2)
    if response.status_code == 200:
        data = response.json()
        answers = [item['data'] for item in data.get('Answer', [])]
        return answers
    else:
        raise Exception(f"DoH request failed with status code {response.status_code}")

def dot_lookup(dns_name, dns_type, dns_server):
    query = dns.message.make_query(dns_name, dns_type)
    response = dns.query.tls(query, dns_server, timeout=2)
    answers = [str(rr) for rr in response.answer[0].items]
    return answers

def api_lookup(dns_name, dns_type, dns_server, protocol, url):
    payload = {
        'dns_name': dns_name,
        'dns_type': dns_type,
        'dns_servers': [dns_server],
        'protocol': protocol
    }
    # Debug: Print the URL and payload
    print(f"API Call URL: {url}")
    print(f"API Call Payload: {json.dumps(payload, indent=2)}")

    response = requests.post(url, json=payload, timeout=10)  # Increased timeout for debugging
    if response.status_code == 200:
        return response.json().get('results', {}).get(dns_server, [])
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
        results = []

        for server_config in config['dns_servers']:
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
                    print(f"Performing local DNS lookup for {dns_name} using {dns_server_ip} and protocol {protocol}")
                    if protocol == 'DoH':
                        answers = doh_lookup(dns_name, dns_type, dns_server_ip)
                    elif protocol == 'DoT':
                        answers = dot_lookup(dns_name, dns_type, dns_server_ip)
                    else:
                        resolver = dns.resolver.Resolver(configure=False)
                        resolver.nameservers = [dns_server_ip]
                        resolver.timeout = 2
                        resolver.lifetime = 2
                        if protocol == 'TCP':
                            resolver.use_tcp = True
                        answers = resolver.resolve(dns_name, dns_type)
                        answers = [str(rdata) for rdata in answers]
                elif url:
                    answers = api_lookup(dns_name, dns_type, dns_server_ip, protocol, url)
                else:
                    print(f"Performing direct DNS lookup for {dns_name} using {dns_server_ip} and protocol {protocol}")
                    if protocol == 'DoH':
                        answers = doh_lookup(dns_name, dns_type, dns_server_ip)
                    elif protocol == 'DoT':
                        answers = dot_lookup(dns_name, dns_type, dns_server_ip)
                    else:
                        resolver = dns.resolver.Resolver(configure=False)
                        resolver.nameservers = [dns_server_ip]
                        resolver.timeout = 2
                        resolver.lifetime = 2
                        if protocol == 'TCP':
                            resolver.use_tcp = True
                        answers = resolver.resolve(dns_name, dns_type)
                        answers = [str(rdata) for rdata in answers]
                server_results["results"].extend(answers)
            except dns.resolver.NoNameservers:
                server_results["results"].append(f"No response from DNS server: {dns_server_ip}")
            except Exception as e:
                server_results["results"].append(str(e))

            results.append(server_results)

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
        results = []

        for server_config in config['dns_servers']:
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
                    print(f"Performing local DNS lookup for {dns_name} using {dns_server_ip} and protocol {protocol}")
                    if protocol == 'DoH':
                        answers = doh_lookup(dns_name, dns_type, dns_server_ip)
                    elif protocol == 'DoT':
                        answers = dot_lookup(dns_name, dns_type, dns_server_ip)
                    else:
                        resolver = dns.resolver.Resolver(configure=False)
                        resolver.nameservers = [dns_server_ip]  # Set the resolver to use only the specified DNS server
                        resolver.timeout = 2  # Set a timeout value to avoid long delays on invalid DNS servers
                        resolver.lifetime = 2  # Set a lifetime value to ensure the query doesn't take too long
                        if protocol == 'TCP':
                            resolver.use_tcp = True
                        answers = resolver.resolve(dns_name, dns_type)
                        answers = [str(rdata) for rdata in answers]
                elif url:
                    answers = api_lookup(dns_name, dns_type, dns_server_ip, protocol, url)
                else:
                    print(f"Performing direct DNS lookup for {dns_name} using {dns_server_ip} and protocol {protocol}")
                    if protocol == 'DoH':
                        answers = doh_lookup(dns_name, dns_type, dns_server_ip)
                    elif protocol == 'DoT':
                        answers = dot_lookup(dns_name, dns_type, dns_server_ip)
                    else:
                        resolver = dns.resolver.Resolver(configure=False)
                        resolver.nameservers = [dns_server_ip]  # Set the resolver to use only the specified DNS server
                        resolver.timeout = 2  # Set a timeout value to avoid long delays on invalid DNS servers
                        resolver.lifetime = 2  # Set a lifetime value to ensure the query doesn't take too long
                        if protocol == 'TCP':
                            resolver.use_tcp = True
                        answers = resolver.resolve(dns_name, dns_type)
                        answers = [str(rdata) for rdata in answers]
                server_results["results"].extend(answers)
            except dns.resolver.NoNameservers:
                server_results["results"].append(f"No response from DNS server: {dns_server_ip}")
            except Exception as e:
                server_results["results"].append(str(e))
            
            results.append(server_results)
    
        print("debug")
        print(results)  # Debug print statement
        return render_template('dns_results.html', dns_name=dns_name, dns_type=dns_type, results=results)
    return render_template('dns_form.html', dns_query_types=dns_query_types)

# Custom root route
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
    # app.run(host='0.0.0.0', port=8080, debug=True)
