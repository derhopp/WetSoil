# WetSoil – Home-Assistant-Bewässerungsintegration

**Experimenteller Entwicklungsstand: Noch nicht für unbeaufsichtigte Bewässerung freigegeben.** Python-Tests, Home-Assistant-Import und hassfest liefen erfolgreich. Eine Installation in einem laufenden Home Assistant sowie Tests mit realen Ventilen stehen aus. HACS meldet aktuell fehlende GitHub-Repository-Beschreibung und Topics.

[English](../README.md) | [Architektur](architecture.md)

## Installation

1. In HACS das benutzerdefinierte Repository https://github.com/derhopp/WetSoil als **Integration** hinzufügen und WetSoil installieren.
2. Home Assistant neu starten, danach Einstellungen → Geräte & Dienste → Integration hinzufügen → WetSoil.
3. Ausschließlich Name und vorhandenen Bereich auswählen. Für jeden Bewässerungskreis eine neue Instanz hinzufügen.
4. Unter Dashboard → Ressourcen das JavaScript-Modul /wetsoil/wetsoil-card.js registrieren, falls noch nicht vorhanden.
5. Die Card custom:wetsoil-card über den Editor hinzufügen und die gewünschte WetSoil-Instanz wählen.

Die Card wird zusammen mit der Integration ausgeliefert und benötigt kein zweites Repository. Die zentrale Konfiguration ist unabhängig von der Dashboard-Konfiguration in Home Assistant gespeichert. Schreiboperationen über WebSocket benötigen Administratorrechte.

## Standardwerte und Konfiguration

Automatik deaktiviert; Basisberegnungszeit 30 Sekunden; Niederschlagsgrenze heute 2,0 mm; durchschnittlicher Regen der letzten drei Tage maximal 2,0 mm/Tag; untere Temperaturgrenze 23 °C; obere 35 °C; Sicherheitslaufzeit maximal 3600 s; Montag–Samstag; April–Oktober; 08:00 Uhr; keine Vorgängerinstanz; keine Ventile.

Über die Card werden Wetter-Entity, optionaler Regen-Binary-Sensor, gemessener Niederschlagssensor und Sensortyp, Ventile, Temperatur-/Niederschlagsgrenzen, Zeitplanung und lineare Verkettung eingestellt. Ventile dürfen nur einem Kreis gehören; mehrere Kreise dürfen dieselbe Wetter-Entity verwenden.

## Wetterdaten

Die Wetter-Entity liefert die tägliche Temperatur- und Regenprognose, soweit der Anbieter geeignete Felder bereitstellt. Temperatur wird in Grad Celsius, Regen in Millimeter normalisiert. Eine stündliche Fallback-Prognose fehlt noch.

Für die historischen Niederschlagsmengen wird ein echter Messsensor benötigt. Unterstützt werden tägliche Summen und kumulative Zähler. Die Integration nimmt etwa alle fünf Minuten Messwerte auf und speichert sie persistent. Mindestens **drei vollständig beobachtete Kalendertage** sind notwendig, bevor der Mittelwert vorliegt. Bei Datenlücken, Sensor-Neustarts oder Zählerrücksetzungen wird der Wert vorsichtig als nicht verfügbar behandelt. Prognosen werden niemals als echte historische Messungen verwendet. Eine automatische Recorder-Rückfüllung fehlt noch.

Der aktuelle Regenzustand wird aus der Wetter-Entity sowie einem optionalen Regen-Binary-Sensor ermittelt. Unbekannte Zustände werden nicht als „kein Regen“ interpretiert.

## Berechnungsalgorithmus

Freigabe nur bei strengem Unterschreiten beider Regen-Grenzen, striktem Überschreiten der unteren Temperaturgrenze und sicher nicht vorhandenem Regen. Bei unbekannten Daten wird keine falsche Null angezeigt. Unterhalb der oberen Temperaturgrenze lautet der Temperaturfaktor 1 + (T - Tmin) / (2 × (Tmax - Tmin)); andernfalls 1,5. Regenfaktoren sind jeweils 1 - Regen / Grenzwert. Dauer: JavaScript Math.round(Basiszeit × alle Faktoren), mindestens die halbe Basiszeit.

Die Card zeigt die wetterabhängig berechnete Dauer getrennt von der tatsächlich geplanten Dauer.

## Bedienung und Sicherheit

Manueller Start ignoriert Automatik-, Wochen- und Monatsfreigaben, niemals jedoch Regensperre, Maximaldauer und Sicherheitszustände. Manuelles Bewässern löst keine Verkettung aus. Ein regulär übersprungener Kreis gibt die automatische Kette weiter, ein fehlgeschlagener Lauf oder ausdrücklicher Stopp nicht. Regen- oder fremde Aktorzustandsänderungen beenden laufende Bewässerungen nicht automatisch.

Schaltbefehle gehen an Home-Assistant-Switch-Entities, ohne automatische Sicherheitsabschaltversuche oder Wiederholungen. Nur ein eigener Lauf wird regulär oder auf ausdrücklichen Stopp beendet. Eine HA-Zustandsrückmeldung garantiert **keine tatsächliche mechanische Ventilstellung**. Unabhängige Hardware-Sicherheitsmaßnahmen sind erforderlich. Nach Neustart werden unterbrochene Bewässerungen nicht fortgesetzt; bereits eingeschaltete Ventile werden dabei nicht ausgeschaltet.

## Bekannte Einschränkungen

Keine validierten Hardwaretests, kein automatisches Nachladen aus Recorder, keine stündliche Forecast-Ergänzung, keine automatisch eingetragene Dashboard-Ressource; einige Entity-Namen im Backend nur auf Englisch; weitere Integrationstests für Parallelität, Zeitumstellungen und Neustarts notwendig.

CI-Ergebnisse: https://github.com/derhopp/WetSoil/actions. Entwicklung erfolgt auf main, ohne Releases oder Tags.


## Aktorsteuerung und externe Absicherung (Änderung vom 16.11.2026)

WetSoil führt **keine eigenständige Sicherheitsabschaltung** aus. Der Anwender muss Abschaltungen bei Fehler, Neustart, Stromausfall und Hängenbleiben eines Ventils außerhalb der Integration absichern. Im Leerlauf sowie bei Start, Entladen, Regen- oder Aktorzustandsänderungen schaltet WetSoil keine Aktoren aus. Externe Bedienung bleibt möglich. Bereits eingeschaltete Aktoren werden bei einem neuen WetSoil-Start nicht übernommen. **Nur für einen von WetSoil gestarteten Bewässerungslauf** sendet die Integration nach Laufzeitende oder ausdrücklichem Stopp einmal den normalen OFF-Befehl, ohne Sicherheits-Retries oder Recovery-Sperren. Beim Entladen wird ein WetSoil-Timer beendet, die Aktoren bleiben unverändert. Ein fehlgeschlagener Teilstart kann bereits aktivierte Aktoren zurücklassen; hier ist ein ausdrücklicher Stopp oder eine externe Abschaltung erforderlich.
