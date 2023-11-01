# Cloudflare DDNS

## Overview
This self-hosted service allows you to perform Dynamic DNS (DDNS) updates using Cloudflare as your DNS provider. You can add, update, and list domains with their associated IP addresses, making it easy to keep your DNS records up to date with changing IP addresses.
### Why I Created This Service
I developed this service to solve the common problem of keeping DNS records synchronized with dynamic IP addresses. With the increasing number of devices hosted on home or small office networks, maintaining accurate DNS records becomes crucial for remote access and service accessibility.

This service provides a lightweight and self-hosted solution that integrates seamlessly with Cloudflare, a popular DNS service provider, ensuring that your domains' IP addresses are always up to date.

## How to Use
Follow these instructions to get started with the Python Cloudflare DDNS Service:

### Prerequisites
Before you begin, make sure you have the following prerequisites in place:
- Docker installed.
- A Cloudflare account with an API token. You can create a token in your [Cloudflare account settings](https://dash.cloudflare.com/profile/api-tokens).
- You need to create A type records before you can update them.
### Installation
1. Start using the included docker-compose.yml:
    ```bash
    docker-compose up -d
    ```
2. Add a domain to the database via:
    ```bash
    curl https://ddns.example.com/add_domain?domain=sub.example.com
    ```
3. Copy the provided token and call an update:
    ```bash
    curl https://ddns.example.com/update?domain=sub.example.com&ip=127.0.0.1&token=tokenprovidedfrombefore
    ```
# TODO
- Add labels to docker-compose.yml
- Add auth to /list
- Add updated when calling /update
- Method to create domains too if missing?
- Change flask to production
- Remove debuging
- Auto build to docker
