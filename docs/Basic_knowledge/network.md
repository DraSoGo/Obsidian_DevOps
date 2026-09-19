#network 
# Networking Fundamentals for DevOps

!!! abstract
    A practical guide to packet flow, addressing, routing, DNS, ports, HTTP, firewalls, and Linux network troubleshooting. The examples build on *Networking Basics* by Abhishek Dere and add concepts used in server, container, and cloud operations.

## Contents

- [Network Mental Model](#network-mental-model)
- [OSI and TCP-IP Layers](#osi-and-tcp-ip-layers)
- [IPv4 Addressing and CIDR](#ipv4-addressing-and-cidr)
- [Switching MAC Addresses and ARP](#switching-mac-addresses-and-arp)
- [Routing and Gateways](#routing-and-gateways)
- [DNS and Name Resolution](#dns-and-name-resolution)
- [TCP UDP and Ports](#tcp-udp-and-ports)
- [HTTP HTTPS and TLS](#http-https-and-tls)
- [NAT and Firewalls](#nat-and-firewalls)
- [Reverse Proxies and Load Balancers](#reverse-proxies-and-load-balancers)
- [Containers and Kubernetes](#containers-and-kubernetes)
- [Linux Network Configuration](#linux-network-configuration)
- [Troubleshooting Workflow](#troubleshooting-workflow)
- [Quick Reference](#quick-reference)
- [Commands That Require Care](#commands-that-require-care)

## Network Mental Model

A client does not send a request directly to an application name. It moves through several decisions and devices:

```text
Application URL
    ↓
DNS resolves a name to an IP address
    ↓
Routing selects an interface and next-hop gateway
    ↓
ARP or NDP resolves the next hop to a link-layer address
    ↓
Switches move frames across the local network
    ↓
Routers move packets between networks
    ↓
Firewalls and NAT inspect or rewrite traffic
    ↓
TCP or UDP delivers data to a port
    ↓
The listening process handles the request
```

For a web application, the complete path may look like:

```text
Browser
  → DNS
  → local route
  → default gateway
  → Internet
  → public firewall / load balancer
  → reverse proxy
  → application container
  → database
```

When a request fails, identify the last layer that works. Avoid restarting unrelated services before locating the break.

## OSI and TCP-IP Layers

The OSI model gives you a shared vocabulary for troubleshooting. Real networks use the TCP/IP model, but the OSI layer numbers remain common in documentation.

| OSI layer | Examples | DevOps questions |
|---|---|---|
| 7 Application | HTTP, DNS, SSH, PostgreSQL | Is the protocol request valid? Does the app return an error? |
| 6 Presentation | TLS, encoding | Does certificate validation or encryption fail? |
| 5 Session | Sessions, connection state | Does a proxy or timeout close the session? |
| 4 Transport | TCP, UDP, ports | Is the port listening? Does the handshake finish? |
| 3 Network | IPv4, IPv6, ICMP, routing | Is there a route to the destination? |
| 2 Data link | Ethernet, Wi-Fi, MAC, VLAN, ARP | Can the host reach the next hop on the local network? |
| 1 Physical | Cable, radio, network interface | Is the link up? Are packets being transmitted? |

Useful shorthand:

- Layer 2: frames within a local network
- Layer 3: packets between IP networks
- Layer 4: TCP/UDP connections and ports
- Layer 7: application protocols and responses

## IPv4 Addressing and CIDR

### Address, prefix, and network

An IPv4 address contains 32 bits. CIDR notation adds a prefix length that defines which bits identify the network.

```text
192.168.1.10/24
│           └── first 24 bits identify the network
└────────────── host address
```

For `192.168.1.10/24`:

| Item | Value |
|---|---|
| Network | `192.168.1.0` |
| Netmask | `255.255.255.0` |
| Usable hosts | `192.168.1.1` to `192.168.1.254` |
| Broadcast | `192.168.1.255` |

Common IPv4 prefixes:

| Prefix | Netmask | Total addresses | Typical use |
|---|---|---:|---|
| `/8` | `255.0.0.0` | 16,777,216 | Large private or provider networks |
| `/16` | `255.255.0.0` | 65,536 | Large internal network |
| `/24` | `255.255.255.0` | 256 | LAN or cloud subnet |
| `/25` | `255.255.255.128` | 128 | Half of a `/24` |
| `/26` | `255.255.255.192` | 64 | Small subnet |
| `/27` | `255.255.255.224` | 32 | Small subnet |
| `/28` | `255.255.255.240` | 16 | Very small subnet |
| `/32` | `255.255.255.255` | 1 | One host or route |

Traditional IPv4 subnets reserve the network and broadcast addresses. Cloud providers may reserve more addresses within each subnet.

### Private, public, and special ranges

Private IPv4 ranges do not route across the public Internet:

```text
10.0.0.0/8
172.16.0.0/12
192.168.0.0/16
```

Other useful ranges:

| Range | Purpose |
|---|---|
| `127.0.0.0/8` | Loopback; `127.0.0.1` is localhost |
| `169.254.0.0/16` | Link-local address, often assigned after DHCP failure |
| `0.0.0.0` | Unspecified address; as a listener, all IPv4 interfaces |
| `0.0.0.0/0` | Default route matching every IPv4 destination |

### Calculate and inspect subnets

```bash
ipcalc 192.168.1.10/24
sudo apt install ipcalc             # Ubuntu or Debian
sudo dnf install ipcalc             # RHEL-based distributions
```

In infrastructure code, check that application, database, load balancer, and container subnets do not overlap. Overlapping CIDRs cause ambiguous routes and block network peering.

## Switching, MAC Addresses, and ARP

### Local switching

A switch forwards Ethernet frames inside one Layer 2 network. It learns which MAC addresses appear on each port.

Two hosts in the same subnet communicate without a router:

```text
Host A                               Host B
192.168.1.10/24  →  Switch  →  192.168.1.11/24
```

Inspect network interfaces and MAC addresses:

```bash
ip link
ip -br link
ip addr
ip -br addr
```

Common interface flags:

| Flag or state | Meaning |
|---|---|
| `UP` | Administratively enabled |
| `LOWER_UP` | Physical or virtual link works |
| `state DOWN` | Interface cannot pass normal traffic |
| `mtu 1500` | Maximum Ethernet IP packet size in bytes |

### ARP and neighbour discovery

IPv4 uses ARP to find the MAC address for a local destination or gateway. IPv6 uses Neighbour Discovery Protocol (NDP).

```bash
ip neigh
ip neigh show 192.168.1.1
```

Common neighbour states:

| State | Meaning |
|---|---|
| `REACHABLE` | The kernel recently confirmed the neighbour |
| `STALE` | Entry exists but needs confirmation before continued use |
| `DELAY` / `PROBE` | The kernel is checking reachability |
| `FAILED` | Address resolution failed |

If a local host cannot reach its gateway, check the interface, VLAN, subnet mask, and neighbour table before investigating DNS.

## Routing and Gateways

### Route selection

A route tells the kernel where to send packets for a destination network. Linux chooses the most specific matching prefix. When two routes have the same prefix, metrics and routing policy determine the choice.

```bash
ip route
ip route get 192.168.2.10
ip route get 1.1.1.1
```

Example table:

```text
default via 192.168.1.1 dev eth0
192.168.1.0/24 dev eth0 proto kernel src 192.168.1.10
192.168.2.0/24 via 192.168.1.254 dev eth0
```

- The connected route reaches the local `192.168.1.0/24` network.
- The static route reaches `192.168.2.0/24` through `192.168.1.254`.
- The default route handles all other destinations through `192.168.1.1`.

### Add temporary routes

```bash
sudo ip route add 192.168.2.0/24 via 192.168.1.254
sudo ip route replace default via 192.168.1.1 dev eth0
sudo ip route del 192.168.2.0/24
```

Commands entered with `ip route` usually disappear after reboot. Configure persistent routes through NetworkManager, Netplan, systemd-networkd, or the distribution's network configuration.

### Default gateway

The default gateway receives traffic for destinations without a more specific route:

```text
Host 192.168.1.10
├── 192.168.1.0/24 → send directly on eth0
├── 192.168.2.0/24 → send to a configured next hop
└── everything else → default gateway 192.168.1.1
```

A next-hop gateway must normally be reachable through a connected route. Adding a route on one host does not create the return route on the destination network.

### Linux as a router

A Linux host needs an interface in each connected network, routes, IP forwarding, and firewall rules that permit forwarded traffic.

```text
Host A                  Linux router                  Host C
192.168.1.5    →    192.168.1.6 | 192.168.2.6   →   192.168.2.5
```

Inspect forwarding:

```bash
sysctl net.ipv4.ip_forward
cat /proc/sys/net/ipv4/ip_forward
```

Enable it until reboot:

```bash
sudo sysctl -w net.ipv4.ip_forward=1
```

Persist it in a file such as `/etc/sysctl.d/99-router.conf`:

```ini
net.ipv4.ip_forward = 1
```

```bash
sudo sysctl --system
```

Forwarding alone does not add routes or open firewall rules. Both endpoint networks need a return path unless the router performs NAT.

## DNS and Name Resolution

### Resolution flow

DNS maps names to records such as IP addresses. Linux may check several sources based on `/etc/nsswitch.conf`:

```text
Application requests db.example.com
    ↓
/etc/nsswitch.conf selects lookup sources
    ↓
/etc/hosts may answer locally
    ↓
Configured DNS resolver receives the query
    ↓
Recursive resolver checks cache or follows DNS delegation
    ↓
Application receives the record and its TTL
```

```bash
grep '^hosts:' /etc/nsswitch.conf
cat /etc/hosts
cat /etc/resolv.conf
resolvectl status
getent hosts db.example.com
```

An entry such as `hosts: files dns` checks `/etc/hosts` before DNS. `/etc/hosts` works for small static overrides, but it does not scale as a service registry.

### DNS hierarchy

DNS reads a fully qualified domain name from right to left:

```text
api.prod.example.com.
│   │    │       │
│   │    │       └── root
│   │    └────────── registered domain
│   └─────────────── subdomain
└─────────────────── host or service label
```

A recursive resolver can contact root, top-level-domain, and authoritative name servers. It caches the answer for the record's TTL.

### Common record types

| Record | Purpose | Example |
|---|---|---|
| `A` | Name to IPv4 address | `api.example.com → 192.0.2.10` |
| `AAAA` | Name to IPv6 address | `api.example.com → 2001:db8::10` |
| `CNAME` | Alias to another name | `www → app.example.net` |
| `MX` | Mail server and priority | `example.com → mail.example.com` |
| `TXT` | Verification and policy text | SPF, DKIM, domain ownership |
| `NS` | Authoritative name server | Zone delegation |
| `SOA` | Zone authority and timing metadata | Primary server and serial |
| `PTR` | Reverse lookup from IP to name | `192.0.2.10 → api.example.com` |
| `SRV` | Service location and port | Service discovery |

A CNAME points to another name, not directly to an IP address. Avoid placing a CNAME alongside other records at the same owner name.

### Search domains

Resolver configuration can append a search suffix to short names:

```text
search example.com prod.example.com
nameserver 192.168.1.100
```

With that configuration, `ssh web` may try `web.example.com`. Use fully qualified names in automation to avoid search-domain ambiguity.

### Query and troubleshoot DNS

```bash
getent hosts api.example.com
dig api.example.com
dig api.example.com A
dig api.example.com AAAA
dig @1.1.1.1 api.example.com
dig +short api.example.com
dig +trace api.example.com
nslookup api.example.com
resolvectl query api.example.com
```

Useful `dig` fields:

| Field | Meaning |
|---|---|
| `status: NOERROR` | Query succeeded; the answer may still be empty |
| `NXDOMAIN` | The queried name does not exist |
| `SERVFAIL` | Resolver or authoritative server could not answer |
| `ANSWER` | Returned records |
| `AUTHORITY` | Servers or records authoritative for the response |
| `SERVER` | Resolver that answered the query |
| `Query time` | Resolver response latency |

Do not edit `/etc/resolv.conf` blindly. NetworkManager, systemd-resolved, DHCP, or container runtimes often generate it.

## TCP, UDP, and Ports

### Transport protocols

TCP provides an ordered byte stream with connection setup, acknowledgements, retransmission, and flow control. UDP sends independent datagrams without connection setup or delivery guarantees.

| Protocol | Common use |
|---|---|
| TCP | HTTP/1.1, HTTP/2, SSH, PostgreSQL, MySQL |
| UDP | DNS queries, DHCP, metrics, voice/video |
| UDP-based QUIC | HTTP/3 |

TCP connection setup uses a three-way handshake:

```text
Client                         Server
  ───── SYN ───────────────────→
  ←────────────── SYN-ACK ──────
  ───── ACK ───────────────────→
```

If SYN packets leave but no SYN-ACK returns, inspect routing, firewalls, security groups, the listener, and the return path.

### Ports and sockets

An IP address identifies a host or interface. A port identifies a service endpoint on that address. A socket combines protocol, local address, local port, and often a remote endpoint.

Common ports:

| Port | Protocol | Service |
|---:|---|---|
| 22 | TCP | SSH |
| 53 | UDP/TCP | DNS |
| 80 | TCP | HTTP |
| 123 | UDP | NTP |
| 443 | TCP/UDP | HTTPS and HTTP/3 |
| 5432 | TCP | PostgreSQL |
| 3306 | TCP | MySQL/MariaDB |
| 6379 | TCP | Redis |
| 6443 | TCP | Kubernetes API |

Inspect listeners and connections:

```bash
sudo ss -lntup
sudo ss -lntp | grep ':443'
ss -tan state established
sudo lsof -iTCP:8080 -sTCP:LISTEN
```

Binding changes reachability:

- `127.0.0.1:8080`: only the local host can connect
- `0.0.0.0:8080`: all IPv4 interfaces can accept traffic
- `[::]:8080`: all IPv6 interfaces, and sometimes IPv4 depending on system settings

Test a port without relying on the application protocol:

```bash
nc -vz server.example.com 443
timeout 3 bash -c '</dev/tcp/server.example.com/443'
```

## HTTP, HTTPS, and TLS

### HTTP request path

```text
Client → load balancer → reverse proxy → application → database
```

An HTTP request contains a method, target, headers, and optional body. The server returns a status code, headers, and optional body.

| Status range | Meaning | Examples |
|---|---|---|
| `2xx` | Success | `200 OK`, `201 Created`, `204 No Content` |
| `3xx` | Redirect or cache state | `301`, `302`, `304` |
| `4xx` | Client-side request or authorization issue | `400`, `401`, `403`, `404`, `429` |
| `5xx` | Server or upstream failure | `500`, `502`, `503`, `504` |

`502 Bad Gateway` often means a proxy could not get a valid response from its upstream. `504 Gateway Timeout` means it waited too long.

```bash
curl -I https://example.com
curl -v https://example.com/api/health
curl -sS -o /dev/null -w '%{http_code}\n' https://example.com/health
curl --resolve api.example.com:443:192.0.2.10 https://api.example.com/health
```

`--resolve` tests a chosen server IP while preserving the HTTP Host header and TLS server name.

### TLS

TLS authenticates the server and encrypts traffic. A client validates the certificate chain, hostname, validity period, and trusted certificate authority.

```bash
openssl s_client -connect example.com:443 -servername example.com
openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates
```

Common TLS failures include an expired certificate, hostname mismatch, incomplete certificate chain, unsupported protocol, or incorrect system time.

## NAT and Firewalls

### Network address translation

NAT rewrites IP addresses or ports as packets cross a device.

- SNAT changes the source, often allowing private hosts to reach the Internet.
- Masquerading is dynamic SNAT using the outgoing interface address.
- DNAT changes the destination, often implementing port forwarding.

```text
192.168.1.10:45000 → NAT router public IP:62000 → Internet server:443
```

NAT requires connection tracking so return traffic can receive the reverse translation. NAT does not replace firewall policy.

### Firewall layers

A connection may pass through several independent controls:

```text
Cloud security group
  → network ACL
  → host firewall
  → container or Kubernetes policy
  → application authorization
```

Linux may use nftables directly or through UFW/firewalld:

```bash
sudo nft list ruleset
sudo ufw status verbose
sudo firewall-cmd --list-all
```

Check both directions. A request path may work while the return path uses a different route or hits a different rule.

!!! warning
    Keep an existing SSH session open when changing remote firewall rules. Add the required management rule before enabling a default-deny policy.

## Reverse Proxies and Load Balancers

### Reverse proxy

A reverse proxy accepts client requests and sends them to an upstream application. Nginx, HAProxy, Envoy, Traefik, and cloud gateways commonly provide:

- TLS termination
- host- and path-based routing
- authentication or request filtering
- compression and caching
- access logs and metrics

The proxy must reach the upstream address and port. The application may only need to bind to a private address when the proxy runs on the same host or network.

### Load balancer

A load balancer distributes traffic among healthy backends:

```text
Client
  → Load balancer
      ├── app-1:8080
      ├── app-2:8080
      └── app-3:8080
```

Health checks need a stable endpoint that tests the dependency level you intend. A shallow liveness check confirms that the process runs. A readiness check confirms that the instance can receive traffic.

Preserve client and protocol information with headers such as `Forwarded`, `X-Forwarded-For`, `X-Forwarded-Proto`, and `Host`. Trust these headers only from known proxies.

## Containers and Kubernetes

### Container networking

A container usually has its own network namespace, interfaces, routes, and port table. A bridge connects containers on one host; NAT can publish a container port on the host.

```text
Internet → host:8080 → NAT / proxy → container:80
```

```bash
docker network ls
docker network inspect NETWORK
docker inspect CONTAINER
docker exec CONTAINER ip addr
docker exec CONTAINER ip route
docker port CONTAINER
```

Publishing `8080:80` maps host port `8080` to container port `80`. Containers on the same Compose network should connect through the service name and container port, not the published host port.

### Kubernetes networking

Kubernetes normally gives each Pod an IP. Services provide stable virtual addresses and DNS names while Pods change.

```text
Client
  → Ingress or Gateway
  → Service
  → ready Pod endpoint
```

Important objects:

| Object | Network role |
|---|---|
| Pod | Runs containers and owns a network namespace |
| Service | Stable virtual IP and backend selection |
| EndpointSlice | Ready backend addresses for a Service |
| Ingress / Gateway | HTTP or TCP entry point and routing |
| NetworkPolicy | Controls allowed Pod traffic when the CNI enforces it |
| CoreDNS | Resolves cluster service names |

```bash
kubectl get pods -o wide
kubectl get services
kubectl get endpointslices
kubectl describe service SERVICE
kubectl exec POD -- cat /etc/resolv.conf
kubectl exec POD -- nslookup SERVICE.NAMESPACE.svc.cluster.local
```

## Linux Network Configuration

### Inspect current state

```bash
ip -br link
ip -br addr
ip route
ip rule
ip neigh
resolvectl status
sudo ss -lntup
```

### Temporary address configuration

```bash
sudo ip link set eth0 up
sudo ip addr add 192.168.1.10/24 dev eth0
sudo ip addr del 192.168.1.10/24 dev eth0
```

These changes usually disappear after reboot. Use the host's network manager for persistent configuration.

### NetworkManager

```bash
nmcli device status
nmcli connection show
nmcli connection show CONNECTION
sudo nmcli connection up CONNECTION
```

### Netplan

Ubuntu Server often stores Netplan configuration under `/etc/netplan/`:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.10/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1, 8.8.8.8]
```

```bash
sudo netplan generate
sudo netplan try
sudo netplan apply
```

Use `netplan try` during remote changes because it can roll back an unconfirmed configuration.

### Packet capture and path inspection

```bash
tracepath example.com
traceroute example.com
mtr example.com
sudo tcpdump -ni any host 192.168.1.10
sudo tcpdump -ni eth0 'tcp port 443'
sudo tcpdump -ni eth0 'port 53'
```

Packet capture shows whether traffic enters or leaves an interface. It does not prove that an application processed the packet.

## Troubleshooting Workflow

### Start from the client and move one layer at a time

1. Confirm the requested hostname, address, port, and protocol.
2. Resolve the hostname and record the returned IP.
3. Check the local interface and chosen route.
4. Test the gateway and destination reachability.
5. Test the destination port.
6. Inspect firewalls, NAT, and load balancers.
7. Confirm that a process listens on the expected address.
8. Send an application-level request.
9. Read logs at each component that handled the request.

### Diagnostic sequence

```bash
# 1. Local interface
ip -br link
ip -br addr

# 2. DNS
getent hosts api.example.com
dig +short api.example.com

# 3. Route
ip route get 192.0.2.10

# 4. Basic reachability
ping -c 4 192.168.1.1
ping -c 4 192.0.2.10

# 5. Transport
nc -vz 192.0.2.10 443

# 6. TLS and HTTP
curl -v https://api.example.com/health

# 7. Local server state
sudo ss -lntp | grep ':443'
journalctl -u my-app.service -n 100 --no-pager
```

Ping failure does not prove that a server is down because firewalls may block ICMP. Test the actual application port.

### Interpret common symptoms

| Symptom | Likely area to inspect |
|---|---|
| `Network is unreachable` | Missing interface address or route |
| `No route to host` | Route, neighbour failure, or firewall rejection |
| `Connection refused` | Host reachable but no listener, or active firewall rejection |
| Connection timeout | Dropped firewall traffic, broken route, or unresponsive service |
| `NXDOMAIN` | DNS name does not exist |
| `SERVFAIL` | DNS resolver or authoritative server failure |
| TLS hostname error | Certificate does not cover the requested name |
| HTTP `502` | Proxy cannot get a valid upstream response |
| HTTP `503` | No healthy backend or service unavailable |
| HTTP `504` | Proxy timed out waiting for upstream |

### Server-side packet path

When a remote client cannot reach an application:

```bash
ip route get CLIENT_IP
sudo ss -lntp | grep ':APP_PORT'
sudo tcpdump -ni any "host CLIENT_IP and port APP_PORT"
sudo nft list ruleset
curl -v http://127.0.0.1:APP_PORT
curl -v http://SERVER_IP:APP_PORT
```

This sequence distinguishes an application binding problem from host firewall, routing, or upstream network problems.

## Quick Reference

### Essential inspection commands

| Question | Command |
|---|---|
| Is the interface up? | `ip -br link` |
| Which addresses exist? | `ip -br addr` |
| Which route will Linux use? | `ip route get DESTINATION` |
| Can the gateway respond? | `ping -c 4 GATEWAY` |
| How does the name resolve? | `getent hosts NAME`; `dig NAME` |
| Is the port reachable? | `nc -vz HOST PORT` |
| Which process listens? | `sudo ss -lntup` |
| Does HTTP work? | `curl -v URL` |
| Is TLS valid? | `openssl s_client -connect HOST:443 -servername HOST` |
| Where does the path fail? | `mtr HOST`; `tracepath HOST` |
| Do packets reach the host? | `sudo tcpdump -ni any host HOST` |
| Which firewall rules apply? | `sudo nft list ruleset` |

### Common configuration files

| Path | Purpose |
|---|---|
| `/etc/hosts` | Static local name mappings |
| `/etc/nsswitch.conf` | Name-resolution source order |
| `/etc/resolv.conf` | Resolver configuration, often generated |
| `/etc/netplan/` | Ubuntu Netplan configuration |
| `/etc/NetworkManager/` | NetworkManager configuration |
| `/etc/sysctl.conf`, `/etc/sysctl.d/` | Kernel network settings such as forwarding |

## Commands That Require Care

!!! danger
    Network changes can disconnect a remote session or expose a service. Record the current configuration and keep an independent recovery path before changing routes, addresses, DNS, or firewalls.

| Command or change | Risk | Safer approach |
|---|---|---|
| `ip addr flush dev INTERFACE` | Removes addresses and disconnects the host | Remove one confirmed address |
| Replacing the default route | Breaks remote and Internet access | Add and test a specific route first |
| `nft flush ruleset` | Removes firewall policy | Export the ruleset and use a timed rollback |
| Enabling IP forwarding | Turns the host into a potential traffic path | Add explicit forwarding rules |
| Editing `/etc/resolv.conf` | Change may be overwritten or break DNS | Configure the active network manager |
| Broad `0.0.0.0/0` firewall rule | Exposes a service to the Internet | Restrict source CIDR and port |
| Packet capture | May collect credentials or private payloads | Narrow the interface, host, port, and duration |

For Linux command fundamentals, services, and permissions, see [linux](../Basic_knowledge/linux.md/). For this vault's Proxmox, TrueNAS, and Tailscale topology, see [server_nas_command](../Basic_knowledge/server_nas_command.md/).
