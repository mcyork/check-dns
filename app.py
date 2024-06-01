from flask import Flask, request, render_template, jsonify
from flask_restx import Api, Resource, fields
import dns.resolver

app = Flask(__name__)
api = Api(app, version='1.0', title='DNS Lookup API',
          description='A simple DNS Lookup API. Visit /dns-lookup for the DNS lookup form.',
          prefix='/api',
          doc='/api'  # Serve Swagger UI at /api
          ) 

ns = api.namespace('dns', description='DNS operations')

# Define the allowed DNS query types as an enumeration
dns_query_types = [
    'A', 'AAAA', 'CAA', 'CNAME', 'MX', 'NS', 'PTR', 'SOA',
    'SRV', 'TXT', 'DS', 'DNSKEY', 'NSEC', 'NSEC3', 'RRSIG',
    'TLSA', 'SMIMEA', 'SPF', 'SSHFP'
]

# Define the expected model for the API input
dns_lookup_model = api.model('DNSLookup', {
    'dns_name': fields.String(required=True, description='The DNS name to lookup'),
    'dns_type': fields.String(required=True, description='The DNS query type', enum=dns_query_types),
    'dns_servers': fields.List(fields.String, description='List of DNS servers to query', default=['8.8.8.8', '1.1.1.1'])
})

@ns.route('/lookup')
class DNSLookup(Resource):
    @ns.expect(dns_lookup_model)
    @ns.response(200, 'Success')
    @ns.response(400, 'Validation Error')
    def post(self):
        """Perform a DNS lookup"""
        data = api.payload
        dns_name = data['dns_name']
        dns_type = data['dns_type']
        dns_servers = data.get('dns_servers', ['8.8.8.8', '1.1.1.1'])
        results = {}

        for dns_server_ip in dns_servers:
            results[dns_server_ip] = []
            try:
                resolver = dns.resolver.Resolver()
                resolver.nameservers = [dns_server_ip]
                resolver.timeout = 2
                resolver.lifetime = 2
                answers = resolver.resolve(dns_name, dns_type)
                for rdata in answers:
                    results[dns_server_ip].append(str(rdata))
            except dns.resolver.NoNameservers:
                results[dns_server_ip].append(f"No response from DNS server: {dns_server_ip}")
            except Exception as e:
                results[dns_server_ip].append(str(e))

        response = {
            'dns_name': dns_name,
            'dns_type': dns_type,
            'results': results
        }
        return jsonify(response)

# Add the namespace to the API
api.add_namespace(ns, path='/dns')

# Route to handle DNS lookup form and results
@app.route('/dns-lookup', methods=['GET', 'POST'])
def dns_lookup():
    if request.method == 'POST':
        dns_name = request.form['dns_name']
        dns_type = request.form['dns_type']
        dns_servers = ['8.8.8.8', '1.1.1.1']  # Replace with your specific DNS server IPs
        results = {}

        for dns_server_ip in dns_servers:
            results[dns_server_ip] = []
            try:
                resolver = dns.resolver.Resolver()
                resolver.nameservers = [dns_server_ip]  # Set the resolver to use only the specified DNS server
                resolver.timeout = 2  # Set a timeout value to avoid long delays on invalid DNS servers
                resolver.lifetime = 2  # Set a lifetime value to ensure the query doesn't take too long
                answers = resolver.resolve(dns_name, dns_type)
                for rdata in answers:
                    results[dns_server_ip].append(str(rdata))
            except dns.resolver.NoNameservers:
                results[dns_server_ip].append(f"No response from DNS server: {dns_server_ip}")
            except Exception as e:
                results[dns_server_ip].append(str(e))
        
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
