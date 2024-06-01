
# DNS Lookup Tool

This project provides a simple web-based DNS lookup tool that allows users to compare DNS query results from multiple DNS servers. It is designed to help users understand how split-brain DNS and modern enterprise network configurations, including VPNs and DNS proxies, might impact their DNS queries.

## Overview

The DNS Lookup Tool is a Flask-based web application that allows users to input a DNS name and DNS query type. The tool then queries multiple DNS servers and displays the results for each server. This can help users identify discrepancies and understand how different DNS configurations might affect their ability to resolve domain names.

## Features

- Web-based interface for DNS queries.
- Queries multiple DNS servers and displays results for each.
- Helps identify split-brain DNS issues.
- Useful for environments with VPNs and DNS proxies that might alter DNS responses.
- API for programmatic access to DNS lookup functionality.

## Prerequisites

- Python 3.6 or higher
- Required Python libraries (see `requirements.txt`)

## Installation

1. Clone the repository to your local machine:

```bash
git clone https://github.com/mcyork/check-dns.git
cd check-dns
```

2. Install the required Python libraries:

```bash
pip install -r requirements.txt
```

## Usage

### Running the Web Application

1. Run the Flask application:

```bash
python3 app.py
```

2. Open your web browser and navigate to:

```
http://127.0.0.1:5000/dns-lookup
```

3. Use the form to input the DNS name and query type, then submit the form to see the DNS results from multiple servers.

### Using the API

The API provides programmatic access to the DNS lookup functionality. The API is documented using Swagger and can be accessed at:

```
http://127.0.0.1:5000/api
```

#### Example API Request

To perform a DNS lookup using the API, send a POST request to `/api/dns/lookup` with the following JSON payload:

```json
{
  "dns_name": "example.com",
  "dns_type": "A",
  "dns_servers": ["8.8.8.8", "1.1.1.1"]
}
```

### Configuration

- The DNS servers to query are specified in the `dns_lookup` function in `app.py`. You can replace `8.8.8.8` and `1.1.1.1` with the IP addresses of your internal or external DNS servers.

```python
dns_servers = ['8.8.8.8', '1.1.1.1']  # Replace with your specific DNS server IPs
```


## Docker
You can also run this application using Docker. Below are the instructions to build and run the Docker image.

### Prerequisites
Docker installed on your local machine
Building the Docker Image

### Clone the repository to your local machine:

```bash
git clone https://github.com/mcyork/check-dns.git
cd check-dns
```
### Build the Docker image:

```bash
docker build -t dns-lookup-tool .
```

### Running the Docker Container
#### Run the Docker container:

```bash
docker run -p 5000:5000 dns-lookup-tool
```
#### Open your web browser and navigate to:

http://127.0.0.1:5000/dns-lookup
This will start the Flask application in a Docker container and make it accessible on port 5000 of your host machine.

## Example

When a user inputs `mcyork.com` and query type `A`, the application will query the specified DNS servers (e.g., `8.8.8.8` and `1.1.1.1`). The results will be displayed, showing the responses from each DNS server:

```
DNS Name: mcyork.com
DNS Type: A

Results from DNS Server: 8.8.8.8
- 173.236.141.229

Results from DNS Server: 1.1.1.1
- 173.236.141.229
```

## Purpose

This tool is particularly useful for diagnosing DNS issues in complex network environments, such as:

- **Split-brain DNS**: Where internal and external DNS servers provide different responses for the same domain name.
- **VPN DNS Proxy**: Some VPN systems proxy all DNS queries and may return different results, including using CGN (Carrier-Grade NAT) IP addressing.
- **Enterprise Networks**: As networks grow and security measures evolve, understanding the true DNS response can become more challenging.

By providing a way to easily compare DNS responses from multiple servers, this tool helps network administrators and users diagnose and understand DNS resolution issues in their environment.

## License

This project is licensed under the MIT License.
