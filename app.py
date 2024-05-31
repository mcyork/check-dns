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
        dns_server_ip = '8.8.8.8'  # Replace this with your specific DNS server IP
        results = []
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dns_server_ip]  # Set the resolver to use only the specified DNS server
            resolver.timeout = 2  # Set a timeout value to avoid long delays on invalid DNS servers
            resolver.lifetime = 2  # Set a lifetime value to ensure the query doesn't take too long
            answers = resolver.resolve(dns_name, dns_type)
            for rdata in answers:
                results.append(str(rdata))
        except dns.resolver.NoNameservers:
            results.append(f"No response from DNS server: {dns_server_ip}")
        except Exception as e:
            results.append(str(e))
        return render_template('dns_results.html', dns_name=dns_name, dns_type=dns_type, results=results)
    return render_template('dns_form.html')

if __name__ == '__main__':
    app.run(debug=True)
