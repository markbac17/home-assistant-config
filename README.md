# 🏠 Home Assistant Config

Personal Home Assistant configuration — version controlled for easy backup, restore, and optimization.

## 📁 Structure

| File | Description |
|------|-------------|
| `configuration.yaml` | Main HA config — includes ZHA, recorder, logger, Yahoo Finance, HomeKit |
| `automations.yaml` | All automations |
| `scenes.yaml` | Scene definitions |
| `sensors.yaml` | Sensor platform configs |
| `homekit.yaml` | Apple HomeKit bridge config |
| `themes.yaml` | Frontend themes |
| `secrets.yaml` | ⚠️ **NOT committed** — contains MQTT passwords |
| `packages/` | Modular config packages (included via `!include_dir_named`) |
| `esphome/` | ESPHome device YAML configs |

## 🔐 Secrets

Sensitive values are stored in `secrets.yaml` (gitignored).  
Reference them in configs using:
```yaml
password: !secret mqtt_ha_password
```

Current secrets in use:
- `mqtt_ha_password`
- `mqtt_z2m_password`
- `mqtt_esphome_password`

> ⚠️ **Never commit `secrets.yaml` to this repo.**

## 🔧 Integrations in Use

- **ZHA** — Zigbee Home Automation
- **HomeKit** — Apple Home bridge
- **Yahoo Finance** — Stock tracking (TSLA, PLTR, NVDA, VOO, VTI, USDPLN=X)
- **MQTT** — Used by Zigbee2MQTT and ESPHome
- **ESPHome** — Custom ESP32/ESP8266 devices

## 🚀 Getting Started (Restore / New Instance)

1. Clone this repo into your HA config directory
2. Create `secrets.yaml` manually with your actual values (see above)
3. Restart Home Assistant

## 📝 Notes

- CalDAV (iCloud calendar) config is commented out — re-enable if needed
- Wemo static IPs are commented out — re-enable with correct IPs from UniFi
- Recorder excludes `*_linkquality` sensors to reduce DB noise

## 🔄 Update Workflow

```bash
git add .
git commit -m "describe your change"
git push
```
