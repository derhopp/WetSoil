# WetSoil – Home-Assistant-Bewässerungsintegration

**Experimenteller Entwicklungsstand: Noch nicht für unbeaufsichtigte Bewässerung freigegeben.** Python-Tests, Home-Assistant-Import und hassfest liefen erfolgreich. Eine Installation in einem laufenden Home Assistant sowie Tests mit realen Ventilen stehen aus. HACS meldet aktuell fehlende GitHub-Repository-Beschreibung und Topics.

[English](../README.md) | [Architektur](architecture.md)

## Installation

1. In HACS das benutzerdefinierte Repository https://github.com/derhopp/WetSoil als **Integration** hinzufügen und WetSoil installieren.
2. Home Assistant neu starten, danach Einstellungen → Geräte & Dienste → Integration hinzufügen → WetSoil.
3. Ausschließlich Name und vorhandenen Bereich auswählen. Für jeden Bewässerungskreis eine neue Instanz hinzufügen.
4. Bei über die Oberfläche verwalteten Dashboard-Ressourcen wird das JavaScript-Modul `/wetsoil/wetsoil-card.js` beim Start automatisch und ohne Duplikate registriert. Bei YAML-verwalteten Ressourcen weiterhin manuell eintragen und die Ressourcen neu laden.
5. Die Card custom:wetsoil-card über den Editor hinzufügen und die gewünschte WetSoil-Instanz wählen.

Die Card wird zusammen mit der Integration ausgeliefert und benötigt kein zweites Repository. Die zentrale Konfiguration ist unabhängig von der Dashboard-Konfiguration in Home Assistant gespeichert. Schreiboperationen über WebSocket benötigen Administratorrechte.

## Standardwerte und Konfiguration

Automatik deaktiviert; Basisberegnungszeit 30 Sekunden; Niederschlagsgrenze heute 2,0 mm; durchschnittlicher Regen der letzten drei Tage maximal 2,0 mm/Tag; untere Temperaturgrenze 23 °C; obere 35 °C; Sicherheitslaufzeit maximal 3600 s; Montag–Samstag; April–Oktober; 08:00 Uhr; keine Vorgängerinstanz; keine Ventile.

Über die Card werden Wetter-Entity, optionaler Regen-Binary-Sensor, gemessener Niederschlagssensor und Sensortyp, Ventile, Temperatur-/Niederschlagsgrenzen, Zeitplanung und lineare Verkettung eingestellt. Ventile dürfen nur einem Kreis gehören; mehrere Kreise dürfen dieselbe Wetter-Entity verwenden.

## Wetterdaten

WetSoil versucht zuerst eine vollständige Stundenprognose für den **gesamten lokalen Kalendertag**. Fehlen Stundenwerte oder unterstützt die Weather-Entity nur `daily`, wird automatisch die Tagesprognose verwendet. Die Einheiten werden nach °C und mm umgerechnet. Beim Wechsel der Weather-Entity wird der alte Cache sofort ungültig; Werte der bisherigen Quelle dürfen nicht weiter angezeigt werden. Eine Stundenprognose nur für die verbleibenden Tagesstunden ist absichtlich keine vollständige Tagesprognose.

Für historische Niederschlagswerte wird ein echter Messsensor benötigt; unterstützt werden Tagessummen und kumulative Zähler. WetSoil speichert selbst Messwerte und versucht zusätzlich, die vergangenen drei abgeschlossenen Tage aus dem **Home-Assistant-Recorder** zurückzufüllen. Dies gelingt nur bei ausreichend dicht aufgezeichneten, konsistenten Messwerten ohne größere Lücken, zurückgesetzte Zähler oder Einheitenwechsel. Recorder zeichnet unter Umständen nur Zustandsänderungen auf; bei konstanten Sensorwerten ist eine vollständige Abdeckung daher nicht automatisch belegbar. Solche Tage bleiben **nicht verfügbar**, niemals null. Bei lückenhafter Historie sind weiterhin mehrere vollständig überwachte Tage nötig. Prognosen zählen niemals als tatsächliche Messung.

Der aktuelle Regenzustand wird aus der Wetter-Entity sowie einem optionalen Regen-Binary-Sensor ermittelt. Unbekannte Zustände werden nicht als „kein Regen“ interpretiert.

## Berechnungsalgorithmus

Freigabe nur bei strengem Unterschreiten beider Regen-Grenzen, striktem Überschreiten der unteren Temperaturgrenze und sicher nicht vorhandenem Regen. Bei unbekannten Daten wird keine falsche Null angezeigt. Unterhalb der oberen Temperaturgrenze lautet der Temperaturfaktor 1 + (T - Tmin) / (2 × (Tmax - Tmin)); andernfalls 1,5. Regenfaktoren sind jeweils 1 - Regen / Grenzwert. Dauer: JavaScript Math.round(Basiszeit × alle Faktoren), mindestens die halbe Basiszeit.

Die Card zeigt die wetterabhängig berechnete Dauer getrennt von der tatsächlich geplanten Dauer.

## Bedienung und Sicherheit

Manueller Start ignoriert Automatik-, Wochen- und Monatsfreigaben, niemals jedoch Regensperre, Maximaldauer und Sicherheitszustände. Manuelles Bewässern löst keine Verkettung aus. Ein regulär übersprungener Kreis gibt die automatische Kette weiter, ein fehlgeschlagener Lauf oder ausdrücklicher Stopp nicht. Regen- oder fremde Aktorzustandsänderungen beenden laufende Bewässerungen nicht automatisch.

Schaltbefehle gehen an Home-Assistant-Switch-Entities, ohne automatische Sicherheitsabschaltversuche oder Wiederholungen. Nur ein eigener Lauf wird regulär oder auf ausdrücklichen Stopp beendet. Eine HA-Zustandsrückmeldung garantiert **keine tatsächliche mechanische Ventilstellung**. Unabhängige Hardware-Sicherheitsmaßnahmen sind erforderlich. Nach Neustart werden unterbrochene Bewässerungen nicht fortgesetzt; bereits eingeschaltete Ventile werden dabei nicht ausgeschaltet.

## Bekannte Einschränkungen

Keine validierten Hardwaretests; Recorder-Backfill nur mit vollständiger Messabdeckung, bei fehlender Tagesprognose keine Schätzung aus unvollständigen Stundenwerten; bei YAML-verwalteten Dashboards muss die Ressource manuell gepflegt werden; zusätzliche HA-Spracheinstellungen und einzelne Systemmeldungen benötigen weiterhin Praxisprüfung; weitere Integrationstests für Parallelität, Zeitumstellungen und Neustarts notwendig.

CI-Ergebnisse: https://github.com/derhopp/WetSoil/actions. Entwicklung erfolgt auf main, ohne Releases oder Tags.


## Aktorsteuerung und externe Absicherung (Änderung vom 16.11.2026)

WetSoil führt **keine eigenständige Sicherheitsabschaltung** aus. Der Anwender muss Abschaltungen bei Fehler, Neustart, Stromausfall und Hängenbleiben eines Ventils außerhalb der Integration absichern. Im Leerlauf sowie bei Start, Entladen, Regen- oder Aktorzustandsänderungen schaltet WetSoil keine Aktoren aus. Externe Bedienung bleibt möglich. Bereits eingeschaltete Aktoren werden bei einem neuen WetSoil-Start nicht übernommen. **Nur für einen von WetSoil gestarteten Bewässerungslauf** sendet die Integration nach Laufzeitende oder ausdrücklichem Stopp einmal den normalen OFF-Befehl, ohne Sicherheits-Retries oder Recovery-Sperren. Beim Entladen wird ein WetSoil-Timer beendet, die Aktoren bleiben unverändert. Ein fehlgeschlagener Teilstart kann bereits aktivierte Aktoren zurücklassen; hier ist ein ausdrücklicher Stopp oder eine externe Abschaltung erforderlich.


### Alternative: Niederschlagsintensität (gleitende 72 Stunden)

Unter **Art der Niederschlagsmessung** ist nun **Niederschlagsintensität (mm/h)** als dritte Alternative neben `daily` und `total` auswählbar. Unterstützte Einheiten sind `mm/h`, `mm/d`, `in/h`, `in/d`, `cm/h` und `cm/d`. WetSoil integriert die aus dem Recorder abgefragten Intensitätswerte über **exakt die letzten 72 vergangenen Stunden** (mm/h × Stunden). Die so berechnete Niederschlagsmenge in mm wird durch drei geteilt und als mittlerer Tagesniederschlag (mm/Tag) in der bisherigen Node-RED-Formel verwendet.

Es werden keine lokalen Kalendertage vorausgesetzt; Zeitumstellungen ändern das 72-Stunden-Fenster nicht. Unveränderte Werte gelten bis zum nächsten im Recorder registrierten Zustandswechsel. Fehlt der Startzustand oder tritt ein ungültiger bzw. unbekannter Zustand auf, bleibt die gesamte Berechnung nicht verfügbar statt den fehlenden Regen als 0 zu behandeln. `intensity_72h_complete` zeigt eine verwertbare Recorder-Historie an. Die Modi `daily` und `total` bleiben unverändert.

## Tatsächlicher Lauf, übersprungener Startversuch und Reset

Ein geplanter Start, bei dem **keine Ventile tatsächlich eingeschaltet wurden**, zählt nur als *übersprungener Versuch*. Deaktivierte Automatik, unvollständige Wetter-/Niederschlagsdaten, Regen oder andere fehlende Freigaben markieren den Kreis nicht als bewässert. Wird die Startuhrzeit nach hinten auf einen späteren, noch zukünftigen Termin verschoben, darf WetSoil am selben Tag erneut versuchen zu starten.

Derselbe lokale Termin (Datum + HH:MM) wird höchstens einmal geprüft; eine **wirklich gestartete automatische Bewässerung** zählt als Tageslauf und sperrt einen weiteren automatischen Lauf bis zum ausdrücklichen Reset. Das gilt auch bei Verkettungen. Manuelle Bewässerungen werden als tatsächliche Starts angezeigt, verbrauchen aber die Tagesfreigabe der Automatik nicht.

Die Card zeigt „Heute tatsächlich gestartet“, „Automatik heute gestartet“, „Letzter tatsächlicher Start“ und den letzten Skipgrund. **Heutigen Laufstatus zurücksetzen** löscht nur die Tagesmarkierungen der ausgewählten Instanz. Es wird kein Ventil geschaltet und keine Bewässerung sofort ausgelöst. Während eines aktiven oder unvollständig gestarteten WetSoil-Laufs ist die Rücksetzung gesperrt. Der letzte tatsächliche Start bleibt als Historie sichtbar. Frühere `last_attempt`-Daten werden bei Updates nicht als Nachweis für einen tatsächlichen Lauf gewertet.

Das Einschalten der Automatik ist künftig auch bei noch unvollständigen Wetter- und Historienwerten möglich; der geplante Zeitpunkt wird dann ohne tatsächlichen Start mit Grund protokolliert. Die eigenständige Aktorsicherung bleibt außerhalb von WetSoil.


## Weitere HA-Entities, Zahlenformat und Live-Card

Zusätzlich stehen native Home-Assistant-Entities für die Startuhrzeit (`time`) und die Art der Niederschlagsmessung (`select`) zur Verfügung. Die vorhandenen Number-Entities und der Konfigurationssensor verwenden dieselbe zentrale Datenhaltung wie die Card. Gespeicherte Konfigurationen tragen eine Versionskennung und frühere Stände werden bei fehlenden neueren Parametern ergänzt.

Die Card aktualisiert sich über WetSoil-Ereignisse bei Änderungen anderer Cards sowie während aktiver Läufe mit einem Countdown. Ereignis-Abos werden beim Entfernen der Card abgemeldet.

**Rundung:** Niederschlagswerte werden mit 2 Nachkommastellen und Temperaturen mit 1 Nachkommastelle angezeigt und vor den Grenzwertvergleichen entsprechend gerundet. Recorder-Rohwerte bleiben in ihrer gespeicherten Präzision erhalten. Bei Werten unmittelbar an Grenzwerten kann dies gegenüber der früheren Vollpräzisionsberechnung das Ergebnis ändern.

Die Card übersetzt bekannte technische Status-/Fehlerkennungen ins Deutsche oder Englische. Native Status-/Sperrgrund-/Datenqualität-Sensoren zeigen ebenfalls lesbare Texte; die technische Kennung bleibt als Attribut `raw_code` für Automationen vorhanden.
