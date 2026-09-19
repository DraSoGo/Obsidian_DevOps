*Tags: `#linux`*
# Linux Fundamentals for DevOps

!!! abstract
    A practical reference for Linux administration. Learn the filesystem, permissions, processes, services, networking, and shell tools instead of memorizing every command.

## Contents

- [Linux and the Shell](#linux-and-the-shell)
- [Filesystem and Files](#filesystem-and-files)
- [Command-Line Essentials](#command-line-essentials)
- [Users and Permissions](#users-and-permissions)
- [Processes and Jobs](#processes-and-jobs)
- [Services and Systemd](#services-and-systemd)
- [System Resources](#system-resources)
- [Networking and Remote Access](#networking-and-remote-access)
- [Packages and Archives](#packages-and-archives)
- [Bash Scripting](#bash-scripting)
- [Text Processing](#text-processing)
- [Editors](#editors)
- [Troubleshooting Workflow](#troubleshooting-workflow)
- [Commands That Require Care](#commands-that-require-care)

## Linux and the Shell

### Kernel and distributions

Linux is the kernel that manages CPU, memory, disks, networks, processes, and devices. A distribution combines the kernel with system tools, a package manager, repositories, and default configuration. Common server distributions include Ubuntu Server, Debian, Rocky Linux, and AlmaLinux.

```bash
uname -r              # Kernel version
uname -a              # Kernel and system details
cat /etc/os-release   # Distribution and version
```

### Terminal, shell, and prompt

A terminal displays a command-line session. A shell runs inside it and interprets commands.

- `sh`: portable Unix shell interface
- `bash`: common default on Linux servers
- `zsh`: interactive shell with extensive customization
- `fish`: user-friendly interactive shell; not POSIX-compatible

```bash
echo "$SHELL"            # Login shell
ps -p $$ -o comm=        # Shell used by this session
bash --version
```

A prompt such as `drasogo@server:~$` shows the user, host, current directory, and privilege level. `$` usually means a normal user; `#` means root.

## Filesystem and Files

Linux uses one directory tree rooted at `/`.

| Path | Purpose |
|---|---|
| `/etc` | System and service configuration |
| `/home` | Normal users' home directories |
| `/root` | Root user's home directory |
| `/srv` | Data served by applications |
| `/var` | Logs, caches, databases, and changing application data |
| `/var/log` | System and application logs |
| `/mnt` | Administrator-managed mounts |
| `/media` | Removable media |
| `/tmp` | Temporary files |
| `/proc`, `/sys` | Runtime kernel and device information |

Paths beginning with `/` are absolute. Relative paths start from the current directory. `.` means the current directory, `..` its parent, and `~` the user's home.

### Navigate and inspect

```bash
pwd                         # Current directory
ls                          # Directory contents
ls -lah                     # Details, sizes, and hidden files
cd /srv/docker/apps         # Absolute path
cd ..                       # Parent directory
cd ~                        # Home directory
```

Names beginning with `.` are hidden. Use `ls -a` to display them.

### Create, copy, move, and remove

```bash
touch notes.txt
mkdir -p project/config/nginx
cp source.txt destination.txt
cp -r source-dir/ destination-dir/
mv old-name.txt new-name.txt
rm file.txt
rm -r directory/
```

!!! danger
    `rm` does not use a recycle bin. Check the resolved path before using `rm -r` or `rm -rf`.

### Read files

```bash
cat file.txt               # Small files
less file.txt              # Browse large files; press q to quit
head -n 20 file.txt
tail -n 20 file.txt
tail -f /var/log/syslog    # Follow appended lines
```

## Command-Line Essentials

### Redirection and pipes

Processes use standard input (`stdin`), standard output (`stdout`), and standard error (`stderr`).

```bash
command > output.txt       # Replace file with stdout
command >> output.txt      # Append stdout
command 2> errors.txt      # Redirect stderr
command > all.txt 2>&1     # Combine stdout and stderr
command 2>/dev/null        # Discard errors
ps aux | grep nginx        # Pipe output into another command
```

### Search and command lookup

```bash
find /etc -type f -name '*.conf'
find /var/log -type f -mtime -1
grep -n 'error' app.log
grep -Rni 'listen' /etc/nginx
type cd                    # Builtin, alias, or executable
command -v nginx           # Executable used by the shell
whereis nginx              # Binary and manual locations
```

### Chaining and exit status

```bash
command1 && command2       # Continue only after success
command1 || command2       # Run command2 after failure
command1 ; command2        # Run both
echo "$?"                  # Previous exit status
```

Exit status `0` means success; a non-zero value indicates an error.

### Variables, quoting, and expansion

```bash
NAME="server"
echo "$NAME"
env
export APP_ENV=production
TODAY=$(date +%F)
```

- Double quotes expand variables: `"Hello $USER"`
- Single quotes preserve literal text: `'Hello $USER'`
- Wildcards match filenames: `*.log`, `file?.txt`, `[abc]*`
- `$PATH` lists directories searched for commands

Shell configuration commonly lives in `~/.bashrc` or `~/.zshrc`.

```bash
alias ll='ls -lah'

mkcd() {
  mkdir -p "$1" && cd "$1"
}

source ~/.bashrc
```

### History and help

```bash
history
history | grep docker
man rsync
rsync --help
```

Use `Ctrl+R` to search command history and `!!` to repeat the previous command.

## Users and Permissions

### Users and privilege

```bash
whoami
id
groups
sudo command
sudo -i                    # Root shell; exit when finished
```

Use `sudo` only where administrative access is required.

### Permission model

`ls -l` displays permissions for the owner, group, and others. Permissions use `r` (read), `w` (write), and `x` (execute). Numeric values are `r=4`, `w=2`, and `x=1`.

| Mode | Meaning |
|---|---|
| `644` | Owner reads/writes; everyone else reads |
| `600` | Owner reads/writes; no other access |
| `755` | Owner writes; everyone can read/execute |
| `700` | Owner only |

```bash
chmod 600 ~/.ssh/id_ed25519
chmod 755 deploy.sh
chmod u+x deploy.sh
chown user:group file
sudo chown -R drasogo:drasogo /srv/app
chgrp devops file
```

Avoid `chmod 777`; it grants write access to every local user.

## Processes and Jobs

```bash
ps aux
pgrep -a nginx
top
htop
kill PID                   # SIGTERM: request a clean shutdown
kill -9 PID                # SIGKILL: immediate termination
pkill process-name
```

Use SIGKILL only when a process ignores normal termination because it cannot clean up resources.

```bash
long-command &             # Start in background
jobs
fg %1
bg %1
nohup command > app.log 2>&1 &
```

`Ctrl+C` interrupts a foreground process. `Ctrl+Z` suspends it.

## Services and Systemd

Systemd starts and supervises background programs called services. It also manages timers, mounts, sockets, devices, and other unit types. A service unit describes what to run, when to run it, which user owns the process, and how systemd should respond when it exits.

### Unit file locations

| Path | Purpose |
|---|---|
| `/usr/lib/systemd/system/` | Vendor units on RHEL-based distributions |
| `/lib/systemd/system/` | Vendor units on Debian-based distributions |
| `/etc/systemd/system/` | Administrator-created units and local overrides |
| `~/.config/systemd/user/` | Units for one user |

Do not edit vendor files directly because package upgrades can replace them. Create custom units under `/etc/systemd/system/` or use an override:

```bash
sudo systemctl edit nginx.service
systemctl cat nginx.service
systemctl show nginx.service
```

### Anatomy of a service unit

A `.service` file normally contains three sections:

```ini
[Unit]
Description=Short description of the service
Documentation=https://example.com/docs
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=appuser
Group=appuser
WorkingDirectory=/opt/my-app
EnvironmentFile=-/etc/my-app/my-app.env
ExecStartPre=/opt/my-app/configure-db.sh
ExecStart=/usr/bin/python3 /opt/my-app/my_app.py
ExecStartPost=/opt/my-app/report-startup.sh
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

#### `[Unit]`: description and ordering

| Directive | Purpose |
|---|---|
| `Description=` | Human-readable name shown by `systemctl status` |
| `Documentation=` | Documentation URL or manual page |
| `After=` | Start this unit after the listed units; it does not create a dependency |
| `Before=` | Start this unit before the listed units |
| `Wants=` | Add a weak dependency; this unit can still start if the dependency fails |
| `Requires=` | Add a strong dependency; stopping or failing a required unit affects this unit |
| `BindsTo=` | Tie this unit's active state more closely to another unit |

Ordering and dependency are separate concepts. A service that needs the network commonly uses both `Wants=network-online.target` and `After=network-online.target`.

#### `[Service]`: process configuration

| Directive | Purpose |
|---|---|
| `Type=simple` | `ExecStart` is the main foreground process; suitable for many applications |
| `Type=exec` | Like `simple`, but startup succeeds only after systemd executes the binary |
| `Type=oneshot` | Run a task and wait for it to finish |
| `Type=forking` | The program forks into the background and usually needs `PIDFile=` |
| `Type=notify` | The program signals systemd when startup finishes |
| `User=` / `Group=` | Run the process with limited privileges |
| `WorkingDirectory=` | Set the process working directory |
| `Environment=` | Define one or more environment variables |
| `EnvironmentFile=` | Read variables from a file; a leading `-` makes the file optional |
| `ExecStartPre=` | Run a command before the main process |
| `ExecStart=` | Start the main service process |
| `ExecStartPost=` | Run a command after systemd considers the service started |
| `ExecReload=` | Define how `systemctl reload` signals the application |
| `Restart=` | Choose whether systemd restarts an exited process |
| `RestartSec=` | Wait before restarting |

Each `Exec...` value must begin with an executable path. Systemd does not interpret shell operators such as pipes, redirects, or `&&` unless you explicitly call a shell. Prefer a separate script when a command needs shell logic.

Keep the application in the foreground. Do not add `&`, use `nohup`, or make a `Type=simple` application daemonize itself; systemd needs to track the main process.

#### `[Install]`: enablement

`WantedBy=multi-user.target` tells systemd where to link the unit when you enable it. Enabling configures automatic startup; it does not start the service in the current session unless you add `--now`.

```bash
sudo systemctl enable my-app.service
sudo systemctl enable --now my-app.service
sudo systemctl disable --now my-app.service
```

### Build a Python application service

Assume the application is `/opt/my-app/my_app.py` and listens on `127.0.0.1:5000`.

#### Prepare the application account and files

```bash
sudo useradd --system --home /opt/my-app --shell /usr/sbin/nologin my-app
sudo mkdir -p /opt/my-app /etc/my-app
sudo chown -R my-app:my-app /opt/my-app
sudo chmod 750 /opt/my-app
```

Store non-secret configuration in `/etc/my-app/my-app.env`:

```ini
APP_ENV=production
APP_PORT=5000
```

```bash
sudo chown root:my-app /etc/my-app/my-app.env
sudo chmod 640 /etc/my-app/my-app.env
```

Do not put credentials directly in the unit file because `systemctl cat` exposes it. An environment file limits accidental display but does not provide encrypted secret storage.

#### Create the unit

Create `/etc/systemd/system/my-app.service`:

```ini
[Unit]
Description=My Python web application
After=network-online.target
Wants=network-online.target

[Service]
Type=exec
User=my-app
Group=my-app
WorkingDirectory=/opt/my-app
EnvironmentFile=-/etc/my-app/my-app.env
ExecStartPre=/opt/my-app/configure-db.sh
ExecStart=/usr/bin/python3 /opt/my-app/my_app.py
ExecStartPost=/opt/my-app/report-startup.sh
Restart=on-failure
RestartSec=5s

# Basic hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/my-app

[Install]
WantedBy=multi-user.target
```

`ExecStartPre` and `ExecStartPost` are optional. Their scripts must exist, be executable, and return exit status `0`; otherwise systemd marks the service as failed. Remove either directive when the application does not need it.

!!! note
    Python's built-in development server is suitable for learning and local testing. Use a production WSGI server such as Gunicorn for an Internet-facing application.

#### Validate and start

```bash
sudo systemd-analyze verify /etc/systemd/system/my-app.service
sudo systemctl daemon-reload
sudo systemctl enable --now my-app.service
systemctl status my-app.service
curl http://127.0.0.1:5000
```

Run `daemon-reload` after creating or changing any unit file. Restart the service when you need the running process to use the new configuration:

```bash
sudo systemctl daemon-reload
sudo systemctl restart my-app.service
```

### Manage services

```bash
systemctl status my-app.service
systemctl is-active my-app.service
systemctl is-enabled my-app.service
sudo systemctl start my-app.service
sudo systemctl stop my-app.service
sudo systemctl restart my-app.service
sudo systemctl reload my-app.service
sudo systemctl reload-or-restart my-app.service
systemctl --failed
systemctl list-units --type=service
```

Use `reload` only when the unit defines `ExecReload` and the application supports reloading. Otherwise restart it.

### Restart policies and limits

Common `Restart=` values:

| Value | Behavior |
|---|---|
| `no` | Do not restart; this is the default |
| `on-failure` | Restart after errors, signals, or timeouts |
| `always` | Restart after clean and failed exits |

Prevent a failing application from restarting without limit:

```ini
[Unit]
StartLimitIntervalSec=60s
StartLimitBurst=3

[Service]
Restart=on-failure
RestartSec=5s
```

Resource limits such as `LimitNOFILE=`, `LimitNPROC=`, and `LimitCORE=` raise or lower process limits. Use explicit values based on measured requirements. Settings such as `infinity`, used by services like Docker, are rarely appropriate for a small application.

### Logs and troubleshooting

Systemd sends service output to the journal unless the unit redirects it elsewhere.

```bash
journalctl -u my-app.service
journalctl -u my-app.service -n 100 --no-pager
journalctl -u my-app.service -f
journalctl -u my-app.service --since today
journalctl -p err
```

If a service fails:

```bash
systemctl status my-app.service --no-pager -l
journalctl -u my-app.service -b --no-pager
systemctl cat my-app.service
systemctl show my-app.service -p User -p Group -p ExecStart -p EnvironmentFiles
sudo systemd-analyze verify /etc/systemd/system/my-app.service
sudo -u my-app /usr/bin/python3 /opt/my-app/my_app.py
sudo ss -lntp | grep ':5000'
curl -v http://127.0.0.1:5000
```

Check file permissions, executable paths, environment files, port conflicts, and the application's own error output before changing the unit.

## System Resources

### Disks and filesystems

```bash
lsblk -f
df -h
du -sh directory/
du -h --max-depth=1 /var | sort -h
mount
mountpoint /mnt/data
```

### Memory, CPU, and host

```bash
free -h
lscpu
uptime
hostnamectl
date
timedatectl
```

## Networking and Remote Access

### Interfaces, routes, and connectivity

```bash
ip addr
ip link
ip route
ip route get 1.1.1.1
ip neigh
cat /etc/resolv.conf
resolvectl status

ping -c 4 192.168.1.1     # Local gateway
ping -c 4 1.1.1.1         # Internet without DNS
ping -c 4 example.com      # Internet with DNS
curl -I https://example.com
curl -v http://127.0.0.1:8080
sudo ss -lntup             # Listening TCP/UDP sockets
ss -tunap                  # Network connections
```

### Firewall

```bash
sudo ufw status verbose
sudo ufw allow 80/tcp
sudo ufw allow from 192.168.1.0/24 to any port 22 proto tcp
sudo ufw status numbered
sudo ufw delete RULE_NUMBER
```

Keep the current SSH session open while changing remote firewall access.

### SSH and file transfer

```bash
ssh user@server
ssh-keygen -t ed25519 -C "device-name"
ssh-copy-id user@server
scp file.txt user@server:/tmp/
scp -r directory/ user@server:/srv/
rsync -avh --progress source/ user@server:/srv/destination/
```

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
```

## Packages and Archives

### Ubuntu and Debian

```bash
sudo apt update
apt list --upgradable
sudo apt upgrade
sudo apt install package-name
sudo apt remove package-name
sudo apt autoremove
dpkg -l | grep package-name
sudo dpkg -i package.deb
sudo apt -f install
```

### RHEL, CentOS Stream, Rocky Linux, and AlmaLinux

RPM is the package format used by Red Hat-based distributions. The `rpm` command works with individual `.rpm` files and the local package database, but it does not resolve dependencies from repositories.

```bash
sudo rpm -i package.rpm          # Install an RPM file
sudo rpm -U package.rpm          # Install or upgrade an RPM file
sudo rpm -e package-name         # Remove an installed package
rpm -q package-name              # Query an installed package
rpm -qi package-name             # Display package information
rpm -ql package-name             # List files installed by a package
rpm -qf /path/to/file            # Find the package that owns a file
```

DNF is the standard high-level package manager on current Red Hat-based systems. It downloads packages from configured repositories and resolves dependencies. `yum` usually remains available as a compatibility command.

```bash
sudo dnf check-update             # Check for available updates
sudo dnf upgrade                  # Upgrade installed packages
sudo dnf install ansible          # Install a package and dependencies
sudo dnf remove ansible           # Remove a package
dnf search ansible                # Search enabled repositories
dnf info ansible                  # Show package information
dnf list installed                # List installed packages
sudo dnf autoremove               # Remove unused dependencies
sudo dnf clean all                # Clear cached repository data
```

Equivalent YUM syntax:

```bash
sudo yum install ansible
sudo yum remove ansible
yum search ansible
sudo yum update
```

Prefer DNF/YUM over `rpm -i` for normal installation because the package manager handles repositories, dependencies, upgrades, and package history.

### Archives

```bash
tar -cvf archive.tar directory/
tar -xvf archive.tar
tar -czvf archive.tar.gz directory/
tar -xzvf archive.tar.gz
zip -r archive.zip directory/
unzip archive.zip
```

## Bash Scripting

### Minimal safe script

```bash
#!/usr/bin/env bash
set -euo pipefail

readonly SOURCE="${1:?Usage: $0 SOURCE}"
readonly DESTINATION="${2:?Usage: $0 SOURCE DESTINATION}"

if ! -d "$SOURCE"; then
  echo "Source directory not found: $SOURCE" >&2
  exit 1
fi

rsync -avh "$SOURCE/" "$DESTINATION/"
```

```bash
chmod +x script.sh
./script.sh /source /destination
```

| Variable | Meaning |
|---|---|
| `$0` | Script name |
| `$1`, `$2` | Positional arguments |
| `$#` | Number of arguments |
| `$@` | All arguments as separate values |
| `$?` | Previous exit status |
| `$$` | Current shell PID |

```bash
if -f "$FILE"; then
  echo "File exists"
elif -d "$FILE"; then
  echo "Directory exists"
else
  echo "Path not found" >&2
fi

for file in *.log; do
  gzip "$file"
done

while read -r host; do
  ping -c 1 "$host"
done < hosts.txt
```

Common tests include `-e` (exists), `-f` (file), `-d` (directory), `-r` (readable), `-w` (writable), `-x` (executable), and `-z` (empty string).

## Text Processing

| Tool | Typical use | Example |
|---|---|---|
| `wc` | Count lines, words, or bytes | `wc -l app.log` |
| `sort` | Sort lines | `sort names.txt` |
| `uniq` | Count adjacent duplicates | `sort access.log \| uniq -c` |
| `cut` | Select delimited fields | `cut -d: -f1 /etc/passwd` |
| `awk` | Select or transform columns | `awk '{print $1}' access.log` |
| `sed` | Replace or select text | `sed 's/http:/https:/' file` |
| `xargs` | Build commands from input | `find . -name '*.tmp' -print0 \| xargs -0 rm` |

```bash
journalctl -u nginx --since today | grep -i error | tail -n 50
awk '{print $1}' access.log | sort | uniq -c | sort -nr | head
```

## Editors

### Nano

```bash
nano file.txt
sudo nano /etc/fstab
```

- `Ctrl+O`, `Enter`: save
- `Ctrl+X`: exit
- `Ctrl+W`: search

### Vim essentials

Vim starts in Normal mode. Press `i` to insert text and `Esc` to return to Normal mode.

| Action              | Keys                       |
| ------------------- | -------------------------- |
| Save                | `:w`                       |
| Quit                | `:q`                       |
| Save and quit       | `:wq` or `ZZ`              |
| Quit without saving | `:q!`                      |
| Undo / redo         | `u` / `Ctrl+R`             |
| Search              | `/pattern`, then `n` / `N` |
| Go to line          | `:42`                      |
| Top/bottom          | `gg` / `G`                 |
| Delete line         | `dd`                       |
| Copy/paste line     | `yy` / `p`                 |


## Troubleshooting Workflow

1. Define the symptom and when it started.
2. Inspect current state before changing anything.
3. Read the relevant logs.
4. Test one layer at a time.
5. Make one reversible change.
6. Repeat the original test and record the result.

### Service example

```bash
systemctl status nginx
journalctl -u nginx -n 100 --no-pager
sudo nginx -t
sudo ss -lntp | grep ':80'
curl -I http://127.0.0.1
```

### Docker example

```bash
docker compose ps
docker compose logs --tail=100
docker inspect CONTAINER
curl -v http://127.0.0.1:PORT
```

### Network example

```bash
ip addr
ip route
ping -c 4 192.168.1.1
ping -c 4 1.1.1.1
ping -c 4 example.com
```

## Commands That Require Care

!!! danger
    Inspect variables, wildcards, paths, and current state before running commands that delete data or interrupt services.

| Command | Risk |
|---|---|
| `rm -rf PATH` | Permanently deletes a directory tree |
| `chmod -R ... PATH` | Recursively changes permissions |
| `chown -R ... PATH` | Recursively changes ownership |
| `rsync --delete SOURCE/ DEST/` | Deletes extra destination files |
| `kill -9 PID` | Prevents process cleanup |
| `sudo command` | Runs with administrative privileges |

Before pressing Enter:

- Expand variables with `printf '%s\n' "$VARIABLE"`.
- Verify the working directory with `pwd`.
- Preview paths with `ls -ld`.
- Use `rsync --dry-run` or another preview option when available.
- Confirm that a current backup can be restored.

Continue with Git, Docker, CI/CD, infrastructure as code, observability, and cloud platforms. Server-specific commands for this vault are in server_nas_command.
