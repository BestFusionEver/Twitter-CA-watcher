# VPS Kurulumu

Bu rehber güncel Ubuntu LTS sunucular için hazırlandı. Ubuntu 24.04 LTS önerilir.

## 1. Sunucuyu hazırlayın

Tek komutla kurulum yapmak istiyorsanız proje klasöründe şunu çalıştırın:

```bash
sudo bash install.sh
```

Sonra sadece şu iki dosyayı düzenleyin:

```bash
sudo nano /etc/x-ca-watcher.env
sudo nano /etc/x-ca-watcher/config.json
sudo systemctl start x-ca-watcher
```

Manuel kurulum adımları aşağıdadır.

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git python3 python3-venv
```

## 2. Uygulama kullanıcısı oluşturun

```bash
sudo useradd --system --home /opt/x-ca-watcher --shell /usr/sbin/nologin xwatcher
sudo mkdir -p /opt/x-ca-watcher /etc/x-ca-watcher /var/lib/x-ca-watcher
sudo chown -R xwatcher:xwatcher /opt/x-ca-watcher /var/lib/x-ca-watcher
```

## 3. Kodu sunucuya koyun

Git repo kullanıyorsanız:

```bash
sudo git clone YOUR_REPO_URL /opt/x-ca-watcher
sudo chown -R xwatcher:xwatcher /opt/x-ca-watcher
```

Repo yoksa dosyaları `scp` veya `rsync` ile `/opt/x-ca-watcher` altına aktarabilirsiniz.

## 4. Python ortamını kurun

```bash
cd /opt/x-ca-watcher
sudo -u xwatcher python3 -m venv .venv
sudo -u xwatcher .venv/bin/python -m pip install --upgrade pip
sudo -u xwatcher .venv/bin/python -m pip install -r requirements.txt
```

## 5. Config ve secret dosyalarını hazırlayın

```bash
sudo cp /opt/x-ca-watcher/deploy/config.prod.example.json /etc/x-ca-watcher/config.json
sudo cp /opt/x-ca-watcher/deploy/x-ca-watcher.env.example /etc/x-ca-watcher.env
sudo nano /etc/x-ca-watcher/config.json
sudo nano /etc/x-ca-watcher.env
```

`/etc/x-ca-watcher/config.json` içinde izlenecek hesapları yazın:

```json
{
  "accounts": ["hesap1", "hesap2"],
  "include_likes": false,
  "max_results_per_account": 10,
  "state_db": "/var/lib/x-ca-watcher/watcher.sqlite3"
}
```

`/etc/x-ca-watcher.env` içine X Bearer Token ve bildirim bilgilerini girin:

```bash
X_BEARER_TOKEN=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

Dosya izinlerini sıkılaştırın:

```bash
sudo chown root:xwatcher /etc/x-ca-watcher.env
sudo chmod 640 /etc/x-ca-watcher.env
sudo chown -R root:xwatcher /etc/x-ca-watcher
sudo chmod 770 /etc/x-ca-watcher
sudo chmod 660 /etc/x-ca-watcher/config.json
```

## 6. Servisi kurun

```bash
sudo cp /opt/x-ca-watcher/deploy/x-ca-watcher.service /etc/systemd/system/x-ca-watcher.service
sudo systemctl daemon-reload
sudo systemctl enable --now x-ca-watcher
```

Bu servis varsayılan olarak `stream` modunda çalışır. Seçilen hesapların yeni postlarında CA varsa polling beklemeden bildirim göndermeyi hedefler.

## 7. Logları kontrol edin

```bash
sudo systemctl status x-ca-watcher
sudo journalctl -u x-ca-watcher -f
```

## Güncelleme

```bash
cd /opt/x-ca-watcher
sudo git pull
sudo -u xwatcher .venv/bin/python -m pip install -r requirements.txt
sudo systemctl restart x-ca-watcher
```

## Önerilen VPS

Başlangıç için 1 vCPU / 1 GB RAM yeterli olur. Çok hesap takip edecekseniz 2 vCPU / 2 GB RAM daha rahat çalışır. Disk ihtiyacı düşüktür; SQLite state dosyası küçük kalır.
