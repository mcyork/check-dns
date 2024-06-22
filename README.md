
---

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
- **Support for Multiple DNS Protocols**: The tool now supports multiple DNS protocols including UDP, TCP, DoH (DNS over HTTPS), and DoT (DNS over TLS). You can specify the protocol in the configuration file (`config.json`) for each DNS server.
- **Enhanced API Capabilities**: The API has been updated to handle DNS lookups using different protocols. The API will automatically detect if the URL points to a local instance and perform the DNS lookup directly to avoid recursion.
- **Advanced Checkbox**: Provides more detailed DNS query results including TTL, record type, and whether the record is authoritative.
- **Additional DNS Server Option**: Allows users to input custom DNS server IP addresses for querying.

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
  "dns_name": "mcyork.com",
  "dns_type": "A",
  "dns_servers": ["8.8.8.8", "1.1.1.1"],
  "protocol": "UDP"
}
```

### Running the Web Application on Different IPs and Ports

You can run the Flask application on different IP addresses and ports by modifying the `app.run` command in `app.py`:

```python
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
```

### Example `curl` Command

To call the API and perform a DNS lookup, you can use the following `curl` command:

```bash
curl -X POST http://127.0.0.1:5000/api/dns/lookup -H "Content-Type: application/json" -d '{
  "dns_name": "mcyork.com",
  "dns_type": "A",
  "dns_servers": ["8.8.8.8", "1.1.1.1"],
  "protocol": "UDP"
}'
```
Results
```bash
{
  "dns_name": "mcyork.com",
  "dns_type": "A",
  "results": [
    {
      "friendly_name": "Google",
      "results": [
        {
          "authoritative": false,
          "query_name": "mcyork.com.",
          "record": "173.236.141.229",
          "ttl": 0,
          "type": "A"
        }
      ],
      "server": "8.8.8.8"
    },
    {
      "friendly_name": "Cloudflare",
      "results": [
        {
          "authoritative": false,
          "query_name": "mcyork.com",
          "record": "173.236.141.229",
          "ttl": 0,
          "type": "A"
        }
      ],
      "server": "1.1.1.1"
    },
    {
      "friendly_name": "Quad9",
      "results": [
        {
          "authoritative": false,
          "query_name": "mcyork.com.",
          "record": "173.236.141.229",
          "ttl": 1,
          "type": "A"
        }
      ],
      "server": "9.9.9.9"
    }
  ]
}
```


### Configuration

- The DNS servers to query are specified in the `config.json` file. You can replace `8.8.8.8` and `1.1.1.1` with the IP addresses of your internal or external DNS servers.

### Advanced Checkbox

The advanced checkbox, when checked, provides more detailed DNS query results. This includes:

- **TTL**: The time-to-live value for each DNS record.
- **Record Type**: The type of DNS record (e.g., `A`, `CNAME`).
- **Authoritative**: Whether the DNS response is authoritative.

If the advanced checkbox is unchecked, the output is less verbose and only includes the DNS record data.

### Additional DNS Server Option

The form allows users to input custom DNS server IP addresses for querying. This can be useful for testing against internal DNS servers or other specific DNS servers not included in the default configuration.

To add a custom DNS server:

1. Enter the DNS server IP address in the provided field.
2. Submit the form.

The tool will include this DNS server in the query and display the results alongside the default servers.

## Docker (UNTESTED)

You can also run this application using Docker. Below are the instructions to build and run the Docker image.

### Prerequisites

- Docker installed on your local machine

### Building the Docker Image

1. Clone the repository to your local machine:

    ```bash
    git clone https://github.com/mcyork/check-dns.git
    cd check-dns
    ```

2. Build the Docker image:

    ```bash
    docker build -t dns-lookup-tool .
    ```

### Running the Docker Container

1. Run the Docker container:

    ```bash
    docker run -p 5000:5000 dns-lookup-tool
    ```

2. Open your web browser and navigate to:

    ```
    http://127.0.0.1:5000/dns-lookup
    ```

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
