# dyn-ip-dns-service

Python script to update current dynamic IP into DNS service with no captcha (like no-ip) and susbcription.

At this moment is suported the services:

- [NOW-DNS](now-dns.com) 
- [Dynu.com](https://www.dynu.com)

## Prerequisites

Python3 installed and imports (requests,logging,argparse,configparser,yaml,json) accesible (via viertualenv, pip, etc).

Service [NOW-DNS](now-dns.com) and/or [Dynu.com](https://www.dynu.com) signed up and with at least one domain/hostname reserved.

## instalaltion:

clone this repository and configure the config file

# #Configuration

File `config-example.yml` has an example to update IP's:

```yaml
services:
    - name: now-dns
      user: google
      pass: 1234
      hosts:
        - google.com
        - google.es
    - name: dynu
      api_key: 'a_valid_api_key'
```

Currently onlu service name accpted are: `now-dns` and `dynu`. Any other name is not supported.

**Both services must be signed up and reserving a domain/hostname by hand.**

### now-dns.com service configuration

The configuration **needs** next values:

- `name`: with the string `now-dns`
- `user`: with a valid user name.
- `pass`: with a valid password for the `user` given.
- `hosts`: a list with a valid hostnames reserved in the service.

Further doc about API can see here: [NOW-DNS "api"](https://now-dns.com/?m=api)

### dynu.com service configuration

The configuration **needs** next values:

- `name`: with the string `dynu`
- `api_key`: a valid api key configured in the webpage: [Dynu API credentials](https://www.dynu.com/en-US/ControlPanel/APICredentials)

The script asks to the api and update every domain reserved with the new IP if needed.

Further doc about API can see here: [Dynu API](https://www.dynu.com/Support/API)


## Script Logs

Script writes logs in standard output with `INFO` level and in `/tmp/dns_update.log` with `WARNING` log level. 

The file has a _hard coding_ rotation policy: 2 backup files with a `30*1024` max size.

## automatic updates.

The script could be inserted in the `crontab`. Examples:

Every minute:

```cron 
* * * * * /home/user/dyn-ip-dns-service/update_ip.py -c ~/.config-dyn-dns.yml
```

Every minute service in dynu and every 5 minuts now-dns:

```cron 
* * * * * /home/user/dyn-ip-dns-service/update_ip.py -c ~/.config-dynu.yml
*/5 * * * * /home/user/dyn-ip-dns-service/update_ip.py -c ~/.config-now-dns.yml
```

Or by using systemd (clones and configured in `/home/user` for the user `user`)

systemd service file: `/usr/lib/systemd/system/update_external_ip.service`

```
[Unit]
Description=Runs the update external IP service
Wants=update_external_ip.timer
[Service]
User=user
ExecStart=/home/user/dyn-ip-dns-service/update_ip.py -c /home/user/.config-dyn-dns.yml
WorkingDirectory=/home/user/dyn-ip-dns-service
[Install]
WantedBy=default.target
```

Refresh the daemon: `sudo systemctl daemon-reload`

To test service: `sudo systemctl start update_external_ip.service`
View the result:  `systemctl status update_external_ip.service`

systemd timer file: `/usr/lib/systemd/system/update_external_ip.timer`

```
[Unit]
Description=Runs update_external_ip.service 
Requires=update_external_ip.service
[Timer]
Unit=update_external_ip.service
OnBootSec=1m
OnUnitActiveSec=1m 
[Install]
WantedBy=timers.target
```

Refresh the daemon: `sudo systemctl daemon-reload`

To start timer: `sudo systemctl start update_external_ip.timer`
Enable at boot: `sudo systemctl enable update_external_ip.timer`

Check id runs: `systemctl status update_external_ip.timer`
