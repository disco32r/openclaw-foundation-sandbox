# Network Monitoring And Management Domain

Network monitoring and management is a first-class final-system domain. It is not an incidental Home Assistant feature, dashboard widget, or ad hoc ops script.

## Scope

- LAN, WAN, VPN, DNS, DHCP, router, switch, access point, and device reachability.
- Proxmox host, OpenClaw VM, Home Assistant VM, and Windows VM connectivity.
- Service exposure checks for OpenClaw, Home Assistant, dashboards, and mobile channels.
- Device inventory and health status.

## Admission Rule

The domain starts read-only. The first accepted workflow may inventory and report network state, but may not change firewall, DNS, DHCP, VPN, routing, port-forwarding, VLAN, device, or wireless settings.

## Protected Mutations

Any network mutation requires an approval packet with:

- affected systems and blast radius,
- exact apply command or UI action,
- validation command,
- rollback command,
- expected downtime,
- stop condition.

## Evidence Required

- Maintained source or official API/documented device interface.
- Local read-only inventory proof.
- Security review for credentials and device access.
- Rollback proof before any write-capable promotion.

## Anti-Drift

No network integration may become a second scheduler, dashboard authority, or hidden mutation path. Network facts are evidence inputs; OpenClaw tasks, approvals, events, and evidence remain the authority.
