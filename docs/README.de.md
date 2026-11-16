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

Keine validierten Hardwaretests; Recorder-Backfill nur mit vollständiger Messabdeckung, bei fehlender Tagesprognose keine Schätzung aus unvollständigen Stundenwerten; keine automatisch eingetragene Dashboard-Ressource; einige Entity-Namen im Backend nur auf Englisch; weitere Integrationstests für Parallelität, Zeitumstellungen und Neustarts notwendig.

CI-Ergebnisse: https://github.com/derhopp/WetSoil/actions. Entwicklung erfolgt auf main, ohne Releases oder Tags.


## Aktorsteuerung und externe Absicherung (Änderung vom 16.11.2026)

WetSoil führt **keine eigenständige Sicherheitsabschaltung** aus. Der Anwender muss Abschaltungen bei Fehler, Neustart, Stromausfall und Hängenbleiben eines Ventils außerhalb der Integration absichern. Im Leerlauf sowie bei Start, Entladen, Regen- oder Aktorzustandsänderungen schaltet WetSoil keine Aktoren aus. Externe Bedienung bleibt möglich. Bereits eingeschaltete Aktoren werden bei einem neuen WetSoil-Start nicht übernommen. **Nur für einen von WetSoil gestarteten Bewässerungslauf** sendet die Integration nach Laufzeitende oder ausdrücklichem Stopp einmal den normalen OFF-Befehl, ohne Sicherheits-Retries oder Recovery-Sperren. Beim Entladen wird ein WetSoil-Timer beendet, die Aktoren bleiben unverändert. Ein fehlgeschlagener Teilstart kann bereits aktivierte Aktoren zurücklassen; hier ist ein ausdrücklicher Stopp oder eine externe Abschaltung erforderlich.
