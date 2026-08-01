# EVOpt Home Assistant Addon

Dieses Home Assistant Addon bietet eine bequeme Möglichkeit, die [EVOpt](https://github.com/evcc-io/optimizer)-Lösung lokal als Addon in Home Assistant zu betreiben. EVOpt ist eine Optimierungslösung für das Laden von Elektrofahrzeugen, die in Kombination mit [evcc.io/evcc](https://github.com/evcc-io/evcc) verwendet werden kann.

---

## Über EVOpt

EVOpt ist eine Software, um intelligentes, dynamisches Laden von Elektrofahrzeugen basierend auf verschiedenen Parametern, einschließlich Energiepreisen, Verfügbarkeiten und Ladebedarfen, zu optimieren. 

Die Kombination mit [evcc.io/evcc](https://github.com/evcc-io/evcc) ermöglicht das simple und effiziente Management der Ladeinfrastruktur.

---

## Features

- Integration in Home Assistant als eigenständiges Addon
- Vorgebaute Images: Bei neuen Commits im [evcc-io/optimizer](https://github.com/evcc-io/optimizer)-Repository wird das Image automatisch per GitHub Actions gebaut und in der GitHub Container Registry veröffentlicht
- Optimierung der Ladezeiten und -mengen für Elektrofahrzeuge
- Nutzung von Daten und Steuerfunktionen von evcc
- Automatische Anpassung an variable Stromtarife und Energieflüsse

---

## Installation

1. Füge das EVOpt Addon-Repository in Home Assistant hinzu:

   Repository URL:
   ```
   https://github.com/jeremiahpslewis/hassio-evopt
   ```

2. Suche in der Addon-Liste nach "evopt" und installiere das Addon.

3. Starte das Addon. Eine weitere Konfiguration ist nicht erforderlich.

---

## Konfiguration

Das Addon stellt keine Optionen im Home Assistant Addon-Panel bereit — der Container startet direkt den evopt-HTTP-Dienst mit sinnvollen Voreinstellungen.

- **API-Endpunkt:** `http://<home-assistant-host>:7050`
- **Health-Check:** `http://<home-assistant-host>:7050/optimize/health` (wird auch als Watchdog des Addons verwendet)

Fest eingestellte Laufzeitparameter des Images:

| Parameter | Wert | Bedeutung |
|---|---|---|
| `OPTIMIZER_TIME_LIMIT` | `10` | Zeitlimit (Sekunden) pro Optimierungslauf |
| `OPTIMIZER_NUM_THREADS` | `1` | Solver-Threads pro Optimierungslauf |
| Gunicorn-Worker | `2` | Anzahl paralleler Optimierungsprozesse |

Diese Werte sind derzeit nicht über das Addon-Panel konfigurierbar.

### Anbindung an evcc

evcc muss so konfiguriert werden, dass es den evopt-Dienst unter `http://<home-assistant-host>:7050` erreicht. Details zur evcc-seitigen Konfiguration finden sich in der [evcc-Dokumentation](https://docs.evcc.io/) und im [evcc-io/optimizer](https://github.com/evcc-io/optimizer)-Repository.

---

## Verwendung

Nach dem Start des Addons kann evcc den evopt-Dienst zur Berechnung optimaler Ladeprofile für Elektrofahrzeuge nutzen. Die Steuerung erfolgt automatisch und passt sich an Deine individuellen Anforderungen und Stromtarife an.

---

## Links
- evopt Repository: [https://github.com/evcc-io/optimizer](https://github.com/evcc-io/optimizer)
- Addon-Repository: [https://github.com/jeremiahpslewis/hassio-evopt](https://github.com/jeremiahpslewis/hassio-evopt)
- evcc Repository: [https://github.com/evcc-io/evcc](https://github.com/evcc-io/evcc)

---

## Diskussion

https://github.com/evcc-io/evcc/discussions/

---

## Support & Mitwirkung

Für Support, Fragen oder Beiträge zum Addon öffne bitte Issues oder Pull Requests im Repository [jeremiahpslewis/hassio-evopt](https://github.com/jeremiahpslewis/hassio-evopt).

---

## Lizenz

Informationen zur Lizenz des Addons sind im Repository zu finden.

---

*Dieses Addon ist eine Ergänzung zur evcc-Projektlösung für intelligente Elektrofahrzeugladeoptimierung in Home Assistant.*
