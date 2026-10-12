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
   https://github.com/thecem/hassio-evopt
   ```

2. Suche in der Addon-Liste nach "EVOpt" und installiere das Addon.

3. Konfiguriere das Addon über das Home Assistant Addon Panel (siehe Konfiguration unten).

4. Starte das Addon.

---

## Konfiguration

Die Konfiguration erfolgt über die `config`-Sektion des Addons, z.B. in der `options`:

```
# Beispiel-Konfiguration (anpassen nach Bedarf)
evcc_api_url: "http://localhost:7070/api"  # URL zur evcc API
charging_mode: "optimiert"                 # Beispiel-Parameter
max_current: 16                            # Maximale Stromstärke in Ampere
tariffs:
  - "tag"
  - "nacht"
```

Für eine vollständige Beschreibung der Parameter und deren Bedeutung empfiehlt sich die Lektüre der evcc-Dokumentation unter:  
[https://github.com/evcc-io/optimizer](https://github.com/evcc-io/optimizer)

---

## Verwendung

Nach der Konfiguration und dem Start des Addons kommuniziert EVOpt mit evcc, um Ladeprofile für Elektrofahrzeuge optimal zu steuern. Die Steuerung erfolgt automatisch und passt sich an Deine individuellen Anforderungen und Stromtarife an.

---

## Links
- evopt Repository: [https://github.com/evcc-io/optimizer](https://github.com/evcc-io/optimizer)
- EVOpt Repository: [https://github.com/thecem/hassio-evopt](https://github.com/thecem/hassio-evopt)
- evcc Repository: [https://github.com/evcc-io/evcc](https://github.com/evcc-io/evcc)

---

## Disccussion

https://github.com/evcc-io/evcc/discussions/

---

## Support & Mitwirkung

Für Support, Fragen oder Beiträge zum Projekt besuche bitte das Repository und öffne gegebenenfalls Issues oder Pull Requests.

---

## Fork mit dem Add-on-Upstream synchronisieren

Unter **Actions → Sync add-on upstream → Run workflow** auf `main` wird
`thecem/hassio-evopt:main` in den Branch `upstream/thecem-main` übernommen.
Dieser Branch enthält den unveränderten Stand des Add-on-Upstreams.
Der Workflow erstellt einen PR von `sync/addon-upstream` nach `main` oder
aktualisiert den bereits offenen PR einschließlich neuer Änderungen aus `main`.
Ist `main` bereits aktuell, wird kein PR erstellt.

Den PR mit **Create a merge commit** zusammenführen, damit Git die bereits
übernommenen Upstream-Commits bei der nächsten Synchronisierung erkennt.
Squash oder Rebase würden diese Historie verlieren. GitHubs **Update branch**
übernimmt nur Änderungen aus dem PR-Zielbranch; neue Commits aus dem externen
Upstream werden über **Run workflow** geholt.

Falls GitHub die automatische PR-Erstellung blockiert, unter **Settings →
Actions → General → Workflow permissions** die Option **Allow GitHub Actions
to create and approve pull requests** aktivieren. Alternativ kann der im
Workflow-Ergebnis verlinkte PR manuell geöffnet werden. Der Workflow muss
zuerst auf `main` zusammengeführt sein, bevor er dort manuell gestartet werden kann.

Die Synchronisierung erhält die Anpassungen dieses Forks: GHCR-Images,
Optimizer-Pin und `OPTIMIZER_SOLVER=highs`. Bei Konflikten bleibt der lokale
Keepalive-Zeitstempel erhalten; der durch den GHCR-Build ersetzte
Docker-Hub-Updater bleibt gelöscht. Andere Konflikte stoppen den Lauf, ohne
den PR-Branch zu überschreiben. Der Workflow verwendet keine Force-Pushes.
Ein geschlossener, nicht zusammengeführter Sync-PR muss vor einem erneuten
Lauf wieder geöffnet oder sein Branch bewusst umbenannt werden.

Dies synchronisiert nur den Add-on-Upstream `thecem/hassio-evopt`.
Die vorhandene Aktualisierung von `evcc-io/optimizer` bleibt davon unabhängig.
**Build optimizer image** prüft weiterhin stündlich sowie bei manuellem Start
den aktuellen `main`-Commit von `evcc-io/optimizer`, baut beide Architekturen und
aktualisiert anschließend den Pin und die Add-on-Version. Änderungen am Add-on
auf `main` lösen ebenfalls einen Build mit einer neuen Version aus, auch wenn
der Optimizer-Commit unverändert ist. **Validate optimizer
image** baut den im PR gepinnten Stand für amd64 und arm64 und prüft API,
HiGHS und CBC, bevor die Änderung zusammengeführt wird.

---

## Lizenz

Informationen zur Lizenz des Addons sind im Repository zu finden.

---

*Dieses Addon ist eine Ergänzung zur evcc-Projektlösung für intelligente Elektrofahrzeugladeoptimierung in Home Assistant.*
