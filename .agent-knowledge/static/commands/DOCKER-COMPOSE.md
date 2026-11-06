# Rules: Membuat Docker Compose (Optimasi)

Gunakan aturan ini setiap kali membuat atau mengubah `docker-compose.yml` / `compose.yaml`.

## 1. Optimasi image &amp; build

- Gunakan base image kecil: `-alpine` atau `-slim`/distroless (waspada musl pada Alpine untuk beberapa paket Python/Node native).
- WAJIB multi-stage build: stage build terpisah dari stage runtime.
- Pin versi image spesifik (mis. `postgres:16.4-alpine`), JANGAN `latest`. Untuk production sebaiknya pin digest.
- Urutkan Dockerfile agar cache efektif: salin file dependency dulu (`package*.json`, `requirements.txt`, `go.mod`), install, baru salin source.
- Gunakan BuildKit cache mount (`RUN --mount=type=cache,...`) untuk package manager.
- WAJIB ada `.dockerignore` (`.git`, `node_modules`, `.env`, `*.log`, `dist` sesuai kebutuhan, `docker-compose*.yml`).
- Jalankan sebagai user non-root (`USER`), hapus cache package manager dalam layer yang sama (`--no-cache`, `rm -rf /var/lib/apt/lists/*`).
- Gabungkan perintah `RUN` yang berkaitan untuk mengurangi layer.

### 1.1 Siklus hidup image

Gunakan empat perintah berikut untuk mengelola image sepanjang development hingga distribution:

- `docker pull <image>:<tag>`: unduh image yang sudah tersedia dari registry untuk dipakai atau diuji secara lokal.
- `docker build -t <registry>/<namespace>/<image>:<tag> .`: bangun image custom; gunakan tag versi yang spesifik, bukan `latest`.
- `docker push <registry>/<namespace>/<image>:<tag>`: unggah image yang telah diuji ke registry agar dapat dipakai tim atau environment lain.
- `docker rmi <image>:<tag>`: hapus image lokal yang sudah tidak digunakan. Verifikasi target dahulu dengan `docker image ls`; gunakan `docker image prune` untuk membersihkan image dangling secara berkala.

Contoh alur:

```bash
docker pull node:20-alpine
docker build -t registry.example.com/myteam/web:1.0.0 .
docker push registry.example.com/myteam/web:1.0.0
docker rmi registry.example.com/myteam/web:1.0.0
```

## 2. Optimasi runtime di Compose

### 2.1 Wajib di setiap service

- `restart: unless-stopped` (production) atau `no`/`on-failure` (dev/job sekali jalan)
- `init: true` agar proses zombie/sinyal ditangani benar
- `healthcheck` yang ringan (interval 10-30s, timeout 3-5s, retries 3-5, `start_period` sesuai waktu boot)
- `logging` dengan rotasi: 
  ```yaml
  logging:  driver: json-file  options:    max-size: "10m"    max-file: "3"
  
  ```
- `depends_on` dengan `condition: service_healthy` untuk dependensi (DB, cache), bukan sekadar urutan start
- `stop_grace_period` sesuai kebutuhan shutdown aplikasi (default 10s; naikkan untuk DB/worker)

### 2.2 Hardening

- `security_opt: ["no-new-privileges:true"]`
- `cap_drop: [ALL]`, tambahkan `cap_add` hanya yang benar-benar perlu
- `read_only: true` bila aplikasi mendukung; sediakan path tulis yang diperlukan secara eksplisit

### 2.3 Network

- Pisahkan network: `frontend` (publik/proxy) dan `backend` (`internal: true` untuk DB/cache).
- JANGAN publish port database/cache ke host. Jika terpaksa, bind ke localhost: `"127.0.0.1:5432:5432"`.
- Hanya reverse proxy yang publish port 80/443.
- Akses antar service lewat nama service (DNS internal), bukan IP.

### 2.4 Volume

- Gunakan named volume untuk data persisten; bind mount hanya untuk dev (source code, config read-only `:ro`).
- Jangan simpan data penting di writable layer container.

### 2.5 Konfigurasi &amp; secret

- Variabel lewat `.env` / `env_file`; JANGAN hardcode password di compose atau commit `.env` ke git (sediakan `.env.example`).
- Wajibkan variabel penting: `${DB_PASSWORD:?DB_PASSWORD wajib diisi}`.
- Untuk production gunakan `secrets:` (file-based) atau secret manager, bukan environment plaintext bila memungkinkan.

### 2.6 Struktur &amp; keterbacaan

- Jangan pakai key `version:` (sudah obsolete di Compose v2).
- Gunakan YAML anchor/extension (`x-common: &common`) untuk menghindari duplikasi (logging, restart, security_opt).
- Gunakan `profiles:` untuk service opsional (debug, migrate, adminer, test) agar tidak jalan default.
- Gunakan nama project/`container_name` hanya bila perlu (container_name menghambat scaling).

### 2.7 Pemisahan dev vs production

- `compose.yaml` = base (umum), `compose.override.yaml` = dev (bind mount, hot reload, port debug), `compose.prod.yaml` = production (tanpa bind mount dan tanpa port debug).
- Jalankan production dengan `docker compose -f compose.yaml -f compose.prod.yaml up -d`.

## 3. Performa spesifik

- Aplikasi stateless dapat discale: `docker compose up -d --scale app=N` (hindari `container_name` dan port host tetap; gunakan load balancer).
- Database: simpan konfigurasi di file yang di-mount `:ro` bila diperlukan.
- Cache (Redis) letakkan di network yang sama dengan app.
- Hindari bind mount lintas OS di Mac/Windows untuk path I/O berat (gunakan named volume).
- Kecilkan build context dengan `.dockerignore` agar proses build lebih cepat.

## 4. Checklist sebelum menyerahkan hasil

- \[ \] Image dipin versi, memakai varian kecil, multi-stage, `.dockerignore` ada
- \[ \] Healthcheck + `depends_on: service_healthy` terpasang
- \[ \] Logging dirotasi
- \[ \] Port DB/cache tidak terekspos publik
- \[ \] Secret tidak hardcode; `.env.example` tersedia
- \[ \] Network dipisah (backend internal)
- \[ \] Container non-root, `no-new-privileges`, `cap_drop` diterapkan jika memungkinkan
- \[ \] Tidak ada `version:`; tidak ada tag `latest`
- \[ \] Validasi: `docker compose config` tanpa error

## 5. Format jawaban agent

1. Tampilkan asumsi yang relevan, seperti environment dan kebutuhan persistensi data.
2. Berikan file compose lengkap.
3. Sebutkan perintah verifikasi: `docker compose config` dan `docker compose up -d`.

## 6. Template ringkas

```yaml
x-common: &common
  restart: unless-stopped
  init: true
  security_opt: ["no-new-privileges:true"]
  logging:
    driver: json-file
    options: { max-size: "10m", max-file: "3" }

services:
  app:
    <<: *common
    image: myorg/app:1.0.0
    env_file: .env
    depends_on:
      db: { condition: service_healthy }
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:3000/health"]
      interval: 15s
      timeout: 3s
      retries: 3
      start_period: 20s
    networks: [frontend, backend]

  db:
    <<: *common
    image: postgres:16.4-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD:?DB_PASSWORD wajib diisi}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    stop_grace_period: 30s
    networks: [backend]

networks:
  frontend:
  backend:
    internal: true

volumes:
  pgdata:

```
