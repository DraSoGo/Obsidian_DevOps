#network #docker #server #devops #linux 

# What
Command reference สำหรับดูแล home server ทั้ง farm — Ubuntu Docker VM (`192.168.1.48`), Proxmox (`192.168.1.47`), TrueNAS (`192.168.1.38`), Tailscale router (`192.168.1.46`) — shell บน VM คือ fish (ghost text + `Ctrl+R` ค้น history แบบ fuzzy) ดูคำสั่งทั่วไปเพิ่มที่ [[linux]]

![[asset/server/btop-default.png|700]]
> btop หน้าตาเริ่มต้น — กล่อง CPU/MEM/NET/PROC เรียงครบในจอเดียว

![[asset/server/topology.jpg|700]]
> topology ของ farm ทั้งก้อน

> [!info] Aliases บน VM (`~/.config/fish/config.fish`)
> `cat` → batcat · `top` → btop · `df` → duf · `dc` → docker compose · `dps` → docker ps แบบตาราง · `apps` → cd /srv/docker/apps · `hstat` → เช็ค Hermes health · `hb` → รัน Hermes backup

![[asset/server/fish-ghost.png|650]]
> fish บนเครื่องจริง — ghost text (สีเทา) คือคำแนะนำ กด `→` ยอม, dropdown completion กด `Tab`

# Daily Health Check
ชุดเช็คประจำวันหลัง ssh เข้า VM — ไล่จากบนลงล่างไม่เกิน 2 นาทีก็รู้ว่าเครื่องสบายไหม

## df -h
```bash
df -h /
```
พื้นที่ disk ของ root — VM ตัวนี้ root เล็กแค่ 56G และใช้ไปแล้ว ~75% ถ้าเต็มคือ containers ล่มทั้งเครื่อง (บน VM พิมพ์ `df` เฉย ๆ ได้เพราะ alias ไป duf ซึ่งสวยกว่า รวม NAS mounts ทั้ง 5 ในตารางเดียว)

## free -h
```bash
free -h
```
RAM — ให้ดูคอลัมน์ `available` ไม่ใช่ `free` เพราะ Linux เอา RAM ส่วนเกินไปทำ disk cache ไว้แล้ว คืนให้ process ได้เสมอ

## uptime
```bash
uptime
```
Load average 1/5/15 นาที — เครื่อง 2 cores ถ้าเกิน 2 ต่อเนื่องแปลว่าทำงานหนักแล้ว

## dps
```bash
dps
```
(alias ของ `docker ps --format ...`) ตาราง containers ทั้ง 26 ตัวพร้อม status + ports ในจอเดียว — ทุกตัวควรขึ้น `Up ... (healthy)`

![[asset/server/dps-output.png|650]]
> output ของ `dps` บนเครื่องจริง — มองหาคำว่า `healthy` ในคอลัมน์ STATUS เป็นหลัก

## docker compose ps
```bash
docker compose ps
```
เหมือน `dps` แต่เฉพาะ project ที่ตัวเองยืนอยู่ (รันจากใน project dir เช่น `cd /srv/docker/apps/OJ`) — เช็คเจาะลึกทีละแอปตอนแอปนั้นมีปัญหา

## systemctl list-timers
```bash
systemctl list-timers --all | grep backup
```
ตาราง timer สำรองข้อมูลทั้งหมด — คอลัมน์ LAST / NEXT บอกว่าแบ็กอัพล่าสุดรันเมื่อไหร่ ต่อไปเมื่อไหร่ ถ้า LAST กระโดดข้ามไปเป็นวัน ๆ = มีตัวไหนตาย

![[asset/server/list-timers.png|650]]
> `systemctl list-timers --all` — ครึ่งล่างของตารางคือตารางเวลา backup ทั้งหมดของเครื่อง

## hstat
```bash
curl -s http://192.168.1.48:8096/healthz | jq .
```
(alias `hstat`) สุขภาพ Hermes bot — ต้องได้ `"status": "ok"` กับ `"discord": true` ถ้า discord เป็น false = gateway หลุด

## mount
```bash
mount | grep cifs
```
NAS mounts ที่กำลังใช้งาน — ต้องมี 5 ตัว: immich, nextcloud, paperless media, paperless consume, server-backup ขาดตัวไหน backup ของตัวนั้นจะ fail ทันที

# Docker
บริหาร 26 containers ใน 10 compose projects ที่ `/srv/docker/apps/` — คำสั่ง `docker compose ...` รันจากใน project directory (`apps` แล้ว `cd OJ` ฯลฯ)

## docker compose up
```bash
docker compose up -d --build
```
คำสั่ง deploy หลัก — rebuild image แล้ว recreate containers ที่เปลี่ยน รันหลัง `git pull` ทุกครั้ง

```bash
docker compose up -d
```
สตาร์ท containers โดยไม่ rebuild — ใช้ตอนแค่สตาร์ทใหม่ไม่ได้แก้โค้ด

## docker compose logs
```bash
docker compose logs -f --tail=100 backend
```
ไล่ log ของ service `backend` แบบ live (`-f`) เริ่มจาก 100 บรรทัดล่าสุด — เอาชื่อ service ออก = ทุก service ใน project เอา `-f` ออก = อ่านครั้งเดียวจบ

## docker compose exec
```bash
docker compose exec database sh
```
เปิด shell ใน container ที่กำลังรันอยู่

```bash
docker compose exec -T database pg_dump -U postgres ojdb | gzip > backup.sql.gz
```
`-T` ปิด TTY ให้ pipe output สะอาด — หัวใจของทุก backup script บนเครื่องนี้

## docker compose down
```bash
docker compose down
```
หยุด + ลบ containers แต่**คง named volumes** (ข้อมูล database ยังอยู่)

> [!danger] อย่าพิมพ์ `-v` ต่อท้ายโดยไม่ตั้งใจ — `down -v` ลบ volumes รวมถึง PostgreSQL data ทั้งก้อน ให้ `docker volume ls` และแบ็กอัพก่อนเสมอ

## docker inspect
```bash
docker inspect oj_backend --format '{{.State.Health.Status}}'
```
ดึงค่าเดียวแบบ scriptable — field ที่ใช้บ่อย: `.State.Status`, `.Config.Image`, `.NetworkSettings.IPAddress`

## docker logs
```bash
docker logs --tail 100 oj_backend
```
อ่าน log ด้วยชื่อ container (ไม่ใช่ service) — ใช้ได้จากทุกที่ไม่ต้อง cd เข้า project

## docker system df
```bash
docker system df
```
พื้นที่ที่ Docker กิน: images / containers / volumes / build cache — รันก่อน prune เพื่อรู้ว่าจะได้คืนกี่ GB

## lazydocker
```bash
lazydocker
```
Docker TUI ครบจบในจอเดียว — ซ้ายเป็น containers/images/volumes ขวาเป็น logs/stats/config ของตัวที่เลือก ไม่ต้องพิมพ์ชื่อ container ยาว ๆ อีก

![[asset/server/lazydocker.png|650]]
> lazydocker กับรายการ containers ฝั่งซ้าย + logs ฝั่งขวา

| Key | Action |
|---|---|
| `1`–`6` | สลับพาเนล: projects, services, containers, images, volumes, networks |
| `[` `]` | tab ก่อนหน้า / ถัดไปของพาเนลขวา |
| `m` | ดู logs ของตัวที่เลือก |
| `r` / `s` | restart / stop container |
| `E` | เปิด shell ใน container |
| `d` | ลบ container/image/volume |
| `b` | คำสั่ง bulk (เช่น prune images ทีเดียวทั้งก้อน) |
| `/` | filter รายการ |
| `esc` | ย้อนกลับ |

# Network
เช็คเส้นทางเน็ต, firewall, และการเข้าถึงจากข้างนอก

## ip route get
```bash
ip route get 192.168.1.47
```
เช็คว่า packet ไป host นั้นจะออก interface ไหนผ่าน gateway อะไร — คำตอบที่เร็วที่สุดของ "ตอนนี้ traffic ไปไหนนะ? ผ่าน Tailscale หรือเปล่า?"

## ss
```bash
sudo ss -lntp
```
ทุก port TCP ที่ฟังอยู่ + ชื่อ process — ใช้ตอน "port 8080 ถูกใครกิน"

## ping
```bash
ping -c 5 1.1.1.1
```
เน็ตโดยไม่มี DNS — คู่กับ `ping -c 5 example.com` ถ้า IP ได้แต่ชื่อไม่ได้ = ปัญหาอยู่ที่ DNS ไม่ใช่เน็ต

## curl
```bash
curl -I http://127.0.0.1
```
ขอเฉพาะ headers จากตัวเครื่องเอง — bypass DNS และ proxy: ถ้าอันนี้ตอบแต่เว็บจริงไม่ตอบ ปัญหาอยู่ upstream ของตัวแอป

```bash
curl -4 ifconfig.me
```
public IPv4 ของเครื่อง — ยืนยันว่า traffic ออกทางไหน

## nmap
```bash
nmap -sn 192.168.1.0/24
```
สแกนหา host ทั้ง LAN — `-sn` คือ ping scan อย่างเดียว ไม่แตะ ports

## ufw
```bash
sudo ufw status verbose
```
สถานะ firewall เต็มรูปแบบ: default policy + rules + binding ต่อ interface — เช็คก่อนอ้างว่าแอปพังเพราะเข้าไม่ได้

```bash
sudo ufw allow in on tailscale0 to any port 22 proto tcp
```
เปิด SSH เฉพาะบน interface ของ Tailscale — อีกแบบที่ใช้บ่อย: `allow from 192.168.1.0/24 to any port 22 proto tcp`

### tailscale
Mesh VPN เข้าถึง LAN `192.168.1.0/24` จากข้างนอกผ่าน router node `192.168.1.46`

```bash
tailscale status
```
ทุกเครื่องใน tailnet พร้อม IP + เวลาที่เห็นล่าสุด + ใครเป็นคน advertise route ของ LAN

![[asset/server/tailscale-status.png|650]]
> `tailscale status` — บรรทัดที่มีคำว่า `offer`/`advertises routes` คือ subnet router (192.168.1.46)

```bash
tailscale ping hp800-g5
```
ทดสอบเส้นทาง — `via 1.2.3.4:port` = ต่อตรง, `via DERP` = ไปอ้อม relay ของ Tailscale (ช้ากว่า)

```bash
tailscale netcheck
```
วินิจฉัย NAT/relay: ได้ UDP ไหม, DERP ตัวไหนใกล้สุด, latency เท่าไหร่

```bash
sudo tailscale set --accept-routes=true
```
(บนเครื่อง client ข้างนอก) ยอมรับ route `192.168.1.0/24` ที่ router advertise — กลับบ้านแล้ว LAN แปลก ๆ ให้สลับเป็น `false`

```bash
sudo tailscale set --advertise-routes=192.168.1.0/24
```
(บนเครื่อง router) ประกาศ subnet เข้า tailnet — ต้องไปกด approve ใน Tailscale admin console ก่อน

```bash
sudo tailscale funnel --bg 80
```
เปิด port 80 ให้ internet จริงเข้าถึงผ่าน Tailscale — เช็คด้วย `tailscale funnel status`, ปิดทั้งหมดด้วย `sudo tailscale funnel reset`

# Systemd & Logs
ทุกอย่างที่ถูก schedule บนเครื่อง (backup timers, mount checks) คือ systemd timers

## systemctl --failed
```bash
systemctl --failed
```
unit ที่ fail ทั้งหมดในรายการเดียว — จุดแรกที่ควรดูตอนเครื่อง "แปลก ๆ" หลัง reboot

## systemctl status
```bash
systemctl status oj-db-backup.service
```
สถานะ unit ใดก็ได้ + log ล่าสุด + PID — ใช้กับ timer ก็ได้ (`status oj-db-backup.timer`)

## journalctl
```bash
journalctl -u hermes -n 100 --no-pager
```
100 บรรทัดล่าสุดของ unit นั้น

```bash
journalctl -u hermes --since "1 hour ago" -f
```
ตั้งแต่ชั่วโมงที่แล้วแล้ว follow ต่อ — ใช้ `--since today` ก็ได้

```bash
journalctl --disk-usage
```
log กิน disk เท่าไหร่ — ถ้าบวมเกิน 1-2 GB: `sudo journalctl --vacuum-size=500M`

## systemctl cat
```bash
systemctl cat oj-db-backup.timer
```
unit file ตามที่ systemd โหลดจริงรวม override — ตอบคำถาม "timer ตัวนี้มันรันอะไร"

## systemctl enable
```bash
sudo systemctl enable --now hermes-backup.timer
```
เปิดให้รันตอน boot + สตาร์ททันที — one-liner ตอนติดตั้ง timer/service ใหม่

```bash
sudo systemctl daemon-reload
```
**จำเป็น** หลังแก้ unit file ทุกครั้ง — ไม่รัน systemd จะยังใช้ตัวเก่า

# Disk & Files
หาที่หายไปของ disk, คัดลอก, ตรวจ backup

## ncdu
```bash
ncdu -x /
```
"disk ไปไหน" แบบ interactive เดินไล่ทีละ directory — `-x` อยู่ใน filesystem เดียวไม่หลุดไป scan CIFS mounts ที่ช้า กด `d` เพื่อลบ (ถามก่อนเสมอ)

![[asset/server/ncdu.png|650]]
> ncdu เรียง directory ตามขนาดใหญ่สุดก่อน — เดินลงไล่หาตัวการได้เลย

## du
```bash
du -sh /var/lib/docker/volumes/
```
ขนาดรวมของ Docker named volumes — ดูก่อน prune อะไร

## rsync
```bash
rsync -aH --info=progress2 SRC/ DST/
```
สำเนาแบบ archive (`-a` คง permission/เวลา) + hardlinks (`-H`) +  progress bar

```bash
rsync -aH --delete --dry-run SRC/ DST/
```
**พรีวิวก่อน** ว่า `--delete` จะลบอะไร — `--delete` ทำ destination เป็น mirror ของ source (ไฟล์ที่ src ไม่มีจะโดนลบ) ห้ามข้าม dry-run

## gzip
```bash
gzip -t backup.sql.gz
```
ตรวจว่า archive ไม่พัง — ไม่มี output = โครงสร้าง gzip ปกติ (แต่ไม่การันตีว่า SQL ข้างในใช้ได้ ต้องลอง restore จริง)

## tar
```bash
tar -tzf backup.tar.gz
```
ลิสต์ของใน archive โดยไม่แตก — เช็คว่า backup ไม่ว่างเปล่า/ไม่ truncate

## find
```bash
find /srv/docker/apps -name "*.yaml" -mtime -7
```
config อะไรเพิ่งถูกแก้ในสัปดาห์ที่ผ่านมา — ใช้ตอนสืบว่า "เมื่อวานแก้อะไรไป"

## grep
```bash
grep -rn "PATTERN" /srv/docker/apps/OJ/
```
ค้นหาแบบ recursive พร้อม file:line — เพิ่ม `-i` ให้ case-insensitive

# Database (PostgreSQL)
service ชื่อ `database`, container ชื่อ `oj_database` — รันจาก project directory ของ OJ

## psql
```bash
docker compose exec database psql -U postgres -l
```
ลิสต์ databases ทั้งหมด — ยืนยันชื่อ target ก่อนทำอะไรที่ destructive

```bash
docker compose exec database psql -U postgres ojdb -c "SELECT COUNT(*) FROM users;"
```
ยิง SQL บรรทัดเดียวจบ — sanity check ข้อมูลหลัง restore

## pg_dump
```bash
docker compose exec database pg_dump -U postgres -Fc ojdb > dump.pg
```
dump แบบ custom format (`-Fc`) — บีบอัดในตัว + restore แบบเลือกส่วนได้ด้วย pg_restore

## pg_restore
```bash
docker compose exec database pg_restore -U postgres -d ojdb --clean dump.pg
```
restore จาก custom dump — `--clean` ทิ้ง objects เดิมก่อนใส่ใหม่

## restore (plain gzip)
```bash
gzip -dc oj-backup.sql.gz | docker compose exec -T database psql -U postgres ojdb
```
restore จาก plain-text dump ที่บีบไว้ — **เขียนทับ target เต็มตัว** เช็คชื่อ database และ dump ก้อนปัจจุบันเก็บไว้ก่อนเสมอ

# Proxmox
Hypervisor ที่ `192.168.1.47:8006` — ssh เป็น `root@192.168.1.47` แล้วคำสั่งรันบน host

## qm list
```bash
qm list
```
VM ทั้งหมดพร้อมสถานะ — VM ที่รัน Docker คือตัวที่ทำงานจริง

## qm shutdown
```bash
qm shutdown 100
```
ปิดแบบสวยผ่าน guest OS — ใช้ตัวนี้ก่อนเสมอ

```bash
qm stop 100
```
ถอดปลั๊ก — ใช้เฉพาะตอน guest ไม่ตอบสนองแล้ว

## pct
```bash
pct list
```
LXC containers ทั้งหมด — `pct enter 101` คือเปิด shell ข้างใน

## pvesh
```bash
pvesh get /cluster/resources
```
มุมมอง API ดิบ: ทุก node/VM/CT พร้อม cpu+mem — ใช้ script ต่อได้ ไม่ต้องเปิด web UI

# Monitoring (TUI)
เครื่องมือแบบเต็มจอสำหรับดูสถานะแบบ realtime

## btop
```bash
btop
```
monitor ครบจบในจอเดียว: CPU ต่อ core, RAM, disk I/O, network graph, process list — เปิดอันดับแรกเสมอตอน "เครื่องช้า" (พิมพ์ `top` ก็ได้ เพราะ alias)

![[asset/server/btop-proc.png|650]]
> กด `4` เพื่อขยายกล่อง PROC เต็มจอ — เลือก process แล้ว `t`/`k` เพื่อ terminate/kill

| Key | Action |
|---|---|
| `1` `2` `3` `4` | ซ่อน/แสดงกล่อง CPU / MEM / NET / PROC |
| `↑` `↓` | เลือก process · `enter` ดูรายละเอียด |
| `t` | terminate ที่เลือก (SIGTERM) |
| `k` | kill ที่เลือก (SIGKILL) |
| `s` | ส่ง signal อะไรก็ได้ |
| `space` | ขยาย/ยุบ process tree |
| `/` | filter processes |
| `m` / `f2` / `f1` | menu / options / help |
| `q` | ออก |

# Hermes
Discord command center + notification hub บน VM (`:8096`) — ทุก backup script รายงานผ่าน `hermes-notify`

## hermes-notify
```bash
hermes-notify --source test --status failure --detail "wiring check"
```
smoke-test เส้นทางแจ้งเตือน — ควรเห็น 🚨 ใน audit channel ทันที

## backup-hermes
```bash
sudo /usr/local/sbin/backup-hermes.sh
```
(alias `hb`) รัน backup ของ Hermes ด้วยมือ — ผลลัพธ์ไปที่ `/mnt/nas-backup/Hermes/`

# High-Risk Commands

> [!danger] เช็ค target, สถานะปัจจุบัน, และมี backup ที่ใช้ได้ก่อนรันทุกตัวในตารางนี้

| Command | ความเสี่ยง | ทางปลอดภัยกว่า |
|---|---|---|
| `docker compose down -v` | ลบ volumes รวมถึง databases | `docker volume ls` + backup ก่อน |
| `gzip -dc ... \| psql` | เขียนทับ database ปลายทาง | `psql -l` ยืนยันชื่อ + dump ใหม่ก่อน |
| `node dist/scripts/init_db.js` | อาจ drop/recreate tables | อ่าน script ก่อน |
| `rsync --delete` | ลบไฟล์ที่ปลายทางไม่มีในต้นทาง | `--dry-run` ก่อน |
| `rm -rf PATH` | ถาวร | `pwd` + `ls -ld PATH` |
| `qm stop VMID` | ถอดปลั๊ก VM | `qm shutdown` ก่อน |

```text
Inspect → understand → change one thing → verify
```

# Related Topics
- [[linux]] — คำสั่ง Linux ทั่วไป
- [[Docker]] — พื้นฐาน Docker
