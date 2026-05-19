# X CA Watcher

Seçtiğiniz X hesaplarının postlarını ve mümkün olduğunda etkileşimlerini izleyip metin içinde token/kontrat adresi yakalayan bot iskeleti.

## Ne yapar?

- X API v2 ile seçili hesapların son postlarını çeker.
- İsteğe bağlı olarak hesapların beğendiği postları da kontrol etmeyi dener.
- Tweet/post metninde olası kontrat adreslerini yakalar:
  - EVM: `0x...`
  - Solana/Base58 benzeri adresler
  - Sui/Aptos tarzı `0x...::module::name` asset idleri
- Aynı postu tekrar bildirmemek için SQLite state tutar.
- Telegram veya Discord webhook ile bildirim gönderir.

> Not: X API erişimleri plan/tier ve yetki kapsamına göre değişebilir. Bu bot resmi X API endpointleriyle tasarlandı; beğeni/etkileşim endpointleri hesabınızın yetkilerine bağlı olarak kısıtlı olabilir.

## Kurulum

Servis kurmadan denemek için:

```bash
./trial.sh
```

Sonra `.env` ve `config.json` dosyalarını doldurun.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
cp config.example.json config.json
```

`.env` içine en azından şunu girin:

```bash
X_BEARER_TOKEN=...
```

Bildirim için Telegram veya Discord ekleyin:

```bash
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

veya:

```bash
DISCORD_WEBHOOK_URL=...
```

## Çalıştırma

Tek seferlik kontrol:

```bash
python -m x_ca_watcher run --config config.json
```

Sürekli izleme:

```bash
python -m x_ca_watcher watch --config config.json --interval 120
```

Anlık bildirime en yakın mod:

```bash
python -m x_ca_watcher stream --config config.json
```

`stream` modu X Filtered Stream kurallarını seçtiğiniz hesaplara göre ayarlar ve yeni postları bağlantı açık kaldığı sürece yakalar. Beğeniler gibi bazı etkileşimler stream ile gelmeyebilir; onlar için `watch` polling modu gerekir.

Stream çalışırken Telegram'dan takip listesi yönetimi:

```text
/add hesap_adi
/remove hesap_adi
/list
```

Komutlar sadece `.env` içindeki `TELEGRAM_CHAT_ID` sahibinden kabul edilir.

Bildirim göndermeden deneme:

```bash
python -m x_ca_watcher run --config config.json --dry-run
```

Telegram/Discord bildirimi test:

```bash
python -m x_ca_watcher notify-test --config config.json
```

CA yakalama ve bildirim gönderme zamanlarını loglamak için `TIMING_LOGS=1` kullanılır. Kapatmak için `.env` içinde `TIMING_LOGS=0` yazın.

Daha kısa bildirim için `.env` içinde `ALERT_COMPACT=1` kullanın.

## BasedBot otomatik gönderim

Telegram bot tokenı başka bir Telegram botuna mesaj atamaz. BasedBot'a otomatik CA göndermek için kendi Telegram hesabınızla MTProto session açılır.

`.env`:

```bash
BASEDBOT_ENABLED=1
BASEDBOT_USERNAME=based_eth_bot
BASEDBOT_SESSION=state/basedbot.session
TELEGRAM_API_ID=...
TELEGRAM_API_HASH=...
```

İlk giriş:

```bash
python -m x_ca_watcher basedbot-login
```

Sonra stream:

```bash
python -m x_ca_watcher stream --config config.json
```

BasedBot tarafında Quick Buy ve alım miktarı önceden küçük bir değerle ayarlanmış olmalıdır.

## Config

`config.json` içinde izlenecek hesapları kullanıcı adıyla yazın:

```json
{
  "accounts": ["example", "another_example"],
  "include_likes": false,
  "max_results_per_account": 10,
  "state_db": "state/watcher.sqlite3"
}
```

`include_likes: true` yaptığınızda bot `GET /2/users/:id/liked_tweets` endpointini de dener. Bu endpoint her X API planında kullanılamayabilir.

## Test

```bash
python -m unittest discover -s tests
```

## VPS

Ubuntu VPS kurulumu için [DEPLOY.md](DEPLOY.md) dosyasındaki systemd rehberini kullanın. Başlangıç için 1 vCPU / 1 GB RAM yeterli; daha çok hesap ve daha kısa kontrol aralığı için 2 vCPU / 2 GB RAM önerilir.
