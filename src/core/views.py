import os
import shutil
import ipaddress
import threading
import urllib.request
from django.conf import settings

# Блокировка для защиты от одновременного обновления баз несколькими потоками
_geoip_update_lock = threading.Lock()
_last_age_check_ts = 0

# Максимальный возраст баз: 30 дней (в секундах)
MAX_DB_AGE_SECONDS = 30 * 24 * 60 * 60

# Ссылки для автоматического обновления баз в src/metrics/geolocation
GEOIP_SOURCES = {
    "GeoLite2-City.mmdb": "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb",
    "GeoLite2-Country.mmdb": "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb",
    "GeoLite2-ASN.mmdb": "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-ASN.mmdb",
    "tor_exit_nodes.txt": "https://check.torproject.org/torbulkexitlist",
    "vpn_datacenter_ipv4.txt": "https://raw.githubusercontent.com/X4BNet/lists_vpn/main/ipv4.txt",
}

# Ключевые слова для распознавания облачных хостингов и VPN по базе ASN
HOSTING_VPN_KEYWORDS = (
    "amazon", "aws", "google cloud", "microsoft azure", "digitalocean",
    "hetzner", "ovh", "linode", "akamai connected", "vultr", "contabo",
    "m247", "datacamp", "choopa", "leaseweb", "scaleway", "oracle cloud",
    "alibaba", "tencent", "hosting", "datacenter", "data center",
    "server", "cloud", "vpn", "proxy", "nordvpn", "mullvad", "proton"
)

# Ключевые слова для фильтрации поисковых роботов и парсеров
BOT_UA_KEYWORDS = (
    "bot", "crawler", "spider", "headless", "ahrefs", "semrush",
    "mj12bot", "dotbot", "petalbot", "bytespider", "gptbot", "curl", "python-requests"
)

# Оперативный кэш в памяти для списков Tor и VPN
_anon_cache = {
    "tor_mtime": 0,
    "tor_ips": set(),
    "vpn_mtime": 0,
    "vpn_buckets": {},
    "vpn_broad": [],
}


def get_geoip_dir():
    """Возвращает путь к папке с базами: /var/www/janeway/src/metrics/geolocation"""
    geoip_dir = os.path.join(settings.BASE_DIR, 'metrics', 'geolocation')
    os.makedirs(geoip_dir, exist_ok=True)
    return geoip_dir


def get_client_ip(request):
    """Получает реальный IP пользователя за Nginx/Docker"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        return x_real_ip.strip()
    return request.META.get('REMOTE_ADDR', '').strip()


def _download_and_replace_files(geoip_dir, files_to_update):
    """Фоновое скачивание и атомарная замена устаревших баз"""
    if not _geoip_update_lock.acquire(blocking=False):
        return

    try:
        for filename, url in files_to_update:
            if not url:
                continue
            target_path = os.path.join(geoip_dir, filename)
            temp_path = target_path + ".tmp"
            min_size = 100_000 if filename.endswith(".mmdb") else 1_000
            try:
                logger.info(f"[GEOIP] Фоновое обновление базы {filename}...")
                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': 'Mozilla/5.0 (Janeway GeoIP Updater)'}
                )
                with urllib.request.urlopen(req, timeout=60) as response, open(temp_path, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)

                if os.path.exists(temp_path) and os.path.getsize(temp_path) > min_size:
                    shutil.move(temp_path, target_path)
                    logger.info(f"[GEOIP] База {filename} успешно обновлена.")
                elif os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                logger.warning(f"[GEOIP] Не удалось обновить {filename}: {e}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
    finally:
        _geoip_update_lock.release()


def ensure_geoip_dbs_up_to_date(geoip_dir):
    """Проверяет возраст баз (не чаще раза в час). Если файлы старше 30 дней — обновляет в фоне"""
    global _last_age_check_ts
    now = time.time()

    if now - _last_age_check_ts < 3600:
        return
    _last_age_check_ts = now

    files_to_update = []
    for filename, url in GEOIP_SOURCES.items():
        file_path = os.path.join(geoip_dir, filename)
        if not os.path.exists(file_path):
            files_to_update.append((filename, url))
        else:
            try:
                if now - os.path.getmtime(file_path) > MAX_DB_AGE_SECONDS:
                    files_to_update.append((filename, url))
            except OSError:
                pass

    if files_to_update:
        threading.Thread(
            target=_download_and_replace_files,
            args=(geoip_dir, files_to_update),
            daemon=True
        ).start()


def _reload_anon_lists_if_needed(geoip_dir):
    """Загружает и индексирует списки Tor и VPN в память только при обновлении файлов на диске"""
    tor_path = os.path.join(geoip_dir, "tor_exit_nodes.txt")
    if os.path.exists(tor_path):
        try:
            mtime = os.path.getmtime(tor_path)
            if mtime != _anon_cache["tor_mtime"]:
                with open(tor_path, "r", encoding="utf-8", errors="ignore") as f:
                    _anon_cache["tor_ips"] = {
                        line.strip() for line in f
                        if line.strip() and not line.startswith("#")
                    }
                _anon_cache["tor_mtime"] = mtime
        except Exception:
            pass

    vpn_path = os.path.join(geoip_dir, "vpn_datacenter_ipv4.txt")
    if os.path.exists(vpn_path):
        try:
            mtime = os.path.getmtime(vpn_path)
            if mtime != _anon_cache["vpn_mtime"]:
                buckets = {}
                broad = []
                with open(vpn_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        try:
                            net = ipaddress.ip_network(line, strict=False)
                            if net.version == 4:
                                if net.prefixlen < 8:
                                    broad.append(net)
                                else:
                                    first_octet = int(net.network_address) >> 24
                                    buckets.setdefault(first_octet, []).append(net)
                        except ValueError:
                            continue
                _anon_cache["vpn_buckets"] = buckets
                _anon_cache["vpn_broad"] = broad
                _anon_cache["vpn_mtime"] = mtime
        except Exception:
            pass


def check_anonymous_ip(ip, asn_org, geoip_dir):
    """Проверяет IP на принадлежность к VPN, Tor, прокси или хостингу"""
    try:
        import geoip2.database
        for anon_filename in ('GeoLite2-Anonymous-IP.mmdb', 'GeoIP2-Anonymous-IP.mmdb'):
            anon_db_path = os.path.join(geoip_dir, anon_filename)
            if os.path.exists(anon_db_path):
                with geoip2.database.Reader(anon_db_path) as anon_reader:
                    anon_resp = anon_reader.anonymous_ip(ip)
                    return {
                        "is_anonymous": bool(anon_resp.is_anonymous),
                        "is_tor": bool(anon_resp.is_tor_exit_node),
                        "is_vpn_or_proxy": bool(anon_resp.is_anonymous_vpn or anon_resp.is_public_proxy),
                        "is_hosting": bool(anon_resp.is_hosting_provider),
                    }
    except Exception:
        pass

    _reload_anon_lists_if_needed(geoip_dir)

    is_tor = ip in _anon_cache["tor_ips"]
    is_vpn_list = False

    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.version == 4:
            first_octet = int(ip_obj) >> 24
            candidates = _anon_cache["vpn_buckets"].get(first_octet, []) + _anon_cache["vpn_broad"]
            is_vpn_list = any(ip_obj in net for net in candidates)
    except ValueError:
        pass

    asn_lower = (asn_org or "").lower()
    is_hosting_asn = any(kw in asn_lower for kw in HOSTING_VPN_KEYWORDS)

    return {
        "is_anonymous": bool(is_tor or is_vpn_list or is_hosting_asn),
        "is_tor": is_tor,
        "is_vpn_or_proxy": bool(is_vpn_list),
        "is_hosting": bool(is_hosting_asn),
    }


def _migrate_legacy_archive_if_needed(legacy_json_path, jsonl_path):
    """Однократно переносит старые записи из map_stats_archive.json в новый map_stats_archive.jsonl"""
    if os.path.exists(legacy_json_path) and not os.path.exists(jsonl_path):
        try:
            with open(legacy_json_path, 'r', encoding='utf-8') as f:
                old_records = json.load(f)
            if isinstance(old_records, list) and old_records:
                with open(jsonl_path, 'a', encoding='utf-8') as out:
                    for entry in old_records:
                        out.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception:
            pass


def map_analytics_api(request):
    """API для отдачи данных о странах и городах на карту D3.js (Equal Earth и Globe)"""
    stats_file = os.path.join(settings.BASE_DIR, 'metrics', 'map_stats.json')
    stats = {"countries": {}, "cities": {}}

    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                loaded_stats = json.load(f)
                if "countries" not in loaded_stats:
                    stats["countries"] = loaded_stats
                else:
                    stats = loaded_stats
        except Exception:
            pass

    response_data = {
        "countries": {},
        "cities": []
    }

    for code, data in stats.get("countries", {}).items():
        response_data["countries"][code] = data.get("count", 0) if isinstance(data, dict) else data

    for city_key, data in stats.get("cities", {}).items():
        coords = data.get("coords") if isinstance(data, dict) else None
        if isinstance(coords, list) and len(coords) == 2 and coords[0] is not None and coords[1] is not None:
            response_data["cities"].append({
                "name": city_key,
                "coords": [coords[1], coords[0]],  # D3 использует формат [долгота, широта]
                "count": data.get("count", 0)
            })

    return JsonResponse(response_data)


def record_geo_view(request):
    """API для скрытой фиксации реального просмотра, автообновления баз и записи в map_stats_archive.jsonl"""
    metrics_dir = os.path.join(settings.BASE_DIR, 'metrics')
    os.makedirs(metrics_dir, exist_ok=True)

    stats_file = os.path.join(metrics_dir, 'map_stats.json')
    legacy_archive_file = os.path.join(metrics_dir, 'map_stats_archive.json')
    archive_file = os.path.join(metrics_dir, 'map_stats_archive.jsonl')

    ip = get_client_ip(request)
    is_local = (
        not ip
        or ip.startswith('127.')
        or ip.startswith('172.')
        or ip.startswith('192.168.')
        or ip == '::1'
    )

    if is_local:
        return JsonResponse({"status": "recorded"})

    geoip_dir = get_geoip_dir()

    # 1. Проверяем возраст баз в src/metrics/geolocation (если старше 30 дней — обновит в фоне)
    ensure_geoip_dbs_up_to_date(geoip_dir)

    # 2. Читаем текущие счетчики для карты
    stats = {"countries": {}, "cities": {}}
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                loaded_stats = json.load(f)
                if "countries" not in loaded_stats:
                    stats["countries"] = loaded_stats
                else:
                    stats = loaded_stats
        except Exception:
            pass

    country_code = None
    city_name = None
    lat, lon = None, None
    time_zone = None
    asn_number = None
    asn_org = None

    try:
        import geoip2.database

        city_db_path = os.path.join(geoip_dir, 'GeoLite2-City.mmdb')
        country_db_path = os.path.join(geoip_dir, 'GeoLite2-Country.mmdb')
        asn_db_path = os.path.join(geoip_dir, 'GeoLite2-ASN.mmdb')

        # 3. Определение города, координат и страны напрямую из src/metrics/geolocation
        if os.path.exists(city_db_path):
            try:
                with geoip2.database.Reader(city_db_path) as city_reader:
                    resp = city_reader.city(ip)
                    country_code = resp.country.iso_code
                    city_name = resp.city.name
                    lat = resp.location.latitude
                    lon = resp.location.longitude
                    time_zone = resp.location.time_zone
            except Exception:
                pass

        if not country_code and os.path.exists(country_db_path):
            try:
                with geoip2.database.Reader(country_db_path) as country_reader:
                    country_code = country_reader.country(ip).country.iso_code
            except Exception:
                pass

        # Fallback на стандартный GeoIP2 Django, если прямые файлы недоступны
        if not country_code:
            try:
                from django.contrib.gis.geoip2 import GeoIP2
                g = GeoIP2()
                try:
                    city_data = g.city(ip)
                    country_code = city_data.get('country_code')
                    city_name = city_data.get('city')
                    lat = city_data.get('latitude')
                    lon = city_data.get('longitude')
                except Exception:
                    country_code = g.country_code(ip)
            except Exception:
                pass

        # 4. Определение организации / университета / провайдера из GeoLite2-ASN.mmdb
        if os.path.exists(asn_db_path):
            try:
                with geoip2.database.Reader(asn_db_path) as asn_reader:
                    asn_resp = asn_reader.asn(ip)
                    asn_number = f"AS{asn_resp.autonomous_system_number}" if asn_resp.autonomous_system_number else None
                    asn_org = asn_resp.autonomous_system_organization
            except Exception:
                pass

        # 5. Проверка на VPN, Tor, хостинги и поисковых ботов
        anon_data = check_anonymous_ip(ip, asn_org, geoip_dir)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        is_bot = any(b in user_agent.lower() for b in BOT_UA_KEYWORDS)

        # 6. Обновление счетчиков публичной карты (без серверных ботов)
        stats_changed = False
        if not is_bot and not anon_data.get("is_hosting"):
            if country_code:
                if country_code not in stats["countries"]:
                    stats["countries"][country_code] = {"count": 0, "ips": []}
                if ip not in stats["countries"][country_code]["ips"]:
                    stats["countries"][country_code]["count"] += 1
                    stats["countries"][country_code]["ips"].append(ip)
                    stats_changed = True

            if city_name and lat is not None and lon is not None:
                city_key = f"{city_name}, {country_code}"
                if city_key not in stats["cities"]:
                    stats["cities"][city_key] = {"count": 0, "coords": [lat, lon], "ips": []}
                if ip not in stats["cities"][city_key]["ips"]:
                    stats["cities"][city_key]["count"] += 1
                    stats["cities"][city_key]["ips"].append(ip)
                    stats_changed = True

        if stats_changed:
            temp_file = stats_file + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False)
            shutil.move(temp_file, stats_file)

        # 7. Миграция старого архива (если есть) и мгновенная дозапись в map_stats_archive.jsonl
        _migrate_legacy_archive_if_needed(legacy_archive_file, archive_file)

        archive_entry = {
            "timestamp": timezone.now().isoformat(),
            "ip": ip,
            "country_code": country_code,
            "city_name": city_name,
            "lat": lat,
            "lon": lon,
            "timezone": time_zone,
            "asn": asn_number,
            "asn_org": asn_org,
            "anonymous_ip": anon_data,
            "is_bot": is_bot,
            "page_url": request.META.get('HTTP_REFERER', 'Direct'),
            "user_agent": user_agent,
        }

        with open(archive_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(archive_entry, ensure_ascii=False) + '\n')

    except Exception as e:
        logger.warning(f"[GEOIP] Ошибка при обработке IP {ip}: {e}")

    return JsonResponse({"status": "recorded"})