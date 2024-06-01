from flask import Flask, render_template, request
import dns.resolver
# pip install dnspython
 

app = Flask(__name__)

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
    return render_template('dns_form.html')


if __name__ == '__main__':
    app.run(debug=True)
