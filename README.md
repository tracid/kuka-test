# Sackpalettierung mit KUKA KR 3200 PA

KRL-Programm und 3D-Simulation für das Palettieren von Säcken (600 × 400 × 200 mm) auf eine Europalette (1200 × 800 mm), vier Lagen hoch. Der Roboter nimmt die Säcke mit einem Sackgabelgreifer von einer Rollenbahn seitlich der Palette auf. Der TCP liegt in der Mitte des gegriffenen Sacks.

| Datei | Inhalt |
| --- | --- |
| `KRL/Palettierung.src` | Programm (Hauptprogramm und lokale Unterprogramme) |
| `KRL/Palettierung.dat` | Datenliste: Maße, Lagenmuster, Offsets, Geschwindigkeiten, E/A-Nummern, Zähler |
| `simulation/index.html` | 3D-Simulation im Browser mit Satzzeiger im KRL-Code |
| `simulation/embed_krl.py` | überträgt geänderte KRL-Dateien in die Simulation |

## Annahmen

| Punkt | Annahme |
| --- | --- |
| Roboter | KUKA KR QUANTEC PA mit 3195 mm Reichweite (KR 120 / 180 / 240 R3200 PA). Palettierkinematik: der Flansch bleibt immer waagerecht, im Programm ändern sich nur X, Y, Z und A. |
| Steuerung | KR C5 oder KR C4 mit KSS 8.x. Reines KRL, keine Technologiepakete (kein KUKA.PalletTech). |
| Sack | 600 × 400 × 200 mm, Länge in Förderrichtung auf der Rollenbahn |
| Palette | Europalette 1200 × 800 × 144 mm, 4 Säcke je Lage, 4 Lagen = 16 Säcke, Stapelhöhe 944 mm |
| TCP | geometrische Sackmitte, also 100 mm über der Oberkante der Gabelzinken. Werkzeug-Z zeigt wie der Flansch nach unten. |
| Greifer | Gabelzinken greifen von beiden Längsseiten unter den Sack, Ventil „Gabel auf/zu“ mit beiden Endlagen, Niederhalter mit Endlage oben, Sensor „Sack im Greifer“ |
| Aufnahme | Rollenbahn mit Anschlag und Lichtschranke, Übergabe per Handshake an die SPS |

## Lagenbild

Ein Sack mit 600 × 400 mm passt auf 1200 × 800 mm ohne Überstand nur im Raster 2 × 2. Ein echter Verbund ist mit diesem Format ohne Überstand nicht möglich. Deshalb wird jede gerade Lage um 180° gedreht abgelegt, sodass die Ventilseite wechselt, und in gespiegelter Reihenfolge belegt. Die Ladung sollte anschließend gewickelt werden.

```
  Y (800)                                    Rollenbahn / Aufnahme liegt auf dieser Seite
  ^   +-------------+-------------+
  |   |  3  (-X,+Y) |  4  (+X,+Y) |          Zahl     = Ablagereihenfolge Lage 1 und 3
  |   +-------------+-------------+          (VX,VY)  = Anfahrrichtung von außen
  |   |  1  (-X,-Y) |  2  (+X,-Y) |
  |   +-------------+-------------+
  +-------------------------------> X (1200)    Ursprung = Ecke Palettenoberkante (Basis 1)
```

Zuerst werden die Säcke auf der von der Aufnahme abgewandten Seite abgelegt, damit der Greifer nie über bereits liegende Säcke der gleichen Lage fährt. Jeder Sack kommt schräg von außen (Versatz `rVorXY`, `rVorZ`) und wird an die Nachbarn angelegt. Das Muster steht als Tabelle `Muster[Lagentyp, Sack]` in der DAT und lässt sich dort ändern.

## Programmablauf

1. `PalInit`: Werkzeug, Basis (Welt), Geschwindigkeiten, Überschleifen setzen. Daten prüfen. Ausgänge in Grundstellung. Liegt noch ein Sack im Greifer, beginnt der Zyklus mit der Ablage.
2. SAK-Fahrt auf `XHOME`.
3. Schleife bis „Zyklusende“:
   - Palette voll (`nLage > nLagen`): `PaletteWechsel` fährt auf HOME, setzt „Palette voll“, wartet, bis die volle Palette weg und eine leere da ist, und setzt die Zähler zurück.
   - `SackAufnehmen`: PTP über die Aufnahme, Gabel auf, auf Sack warten, LIN schnell bis 60 mm über den Sack, dann langsam bis die Zinken 15 mm unter dem Sack liegen. Gabel zu, Niederhalter ab, Sensor prüfen, LIN hoch. Der Trigger „Sack entnommen“ gibt den Förderer frei, sobald die Gabel aus der Rollenbahn heraus ist.
   - `SackAblegen`: Zielpunkte aus Lagenmuster und Lage berechnen. PTP auf Überfahrhöhe (seitlich versetzt), LIN schräg an die Nachbarn bis 15 mm über die Endlage, Sensor prüfen, Gabel auf, Niederhalter hoch, Zähler weiter, LIN senkrecht hoch.
4. Zyklusende: zurück auf HOME. Die Zähler bleiben erhalten, ein Neustart setzt die Palette fort. Zyklusende beendet auch das Warten auf einen Sack.

Alle Zielpunkte berechnet die Funktion `ZielWelt` aus der Stationsbasis (`BASE_DATA` oder Layout-Frame) und bewegt sich in Weltkoordinaten. B und C sind fest, weil der Flansch beim PA immer waagerecht steht. PTP-Ziele werden als `FRAME` ohne Status und Turn übergeben, die Steuerung wählt dann den Turn mit dem kürzesten Achsweg. Beim ersten Test in T1 die Drehrichtung von A6 beobachten.

Störungen erzeugen Quittiermeldungen über `Set_KrlMsg`: Gabel oder Niederhalter erreichen die Endlage nicht (3 s Überwachung, Quittieren wiederholt), kein Sack nach dem Greifen (erneut greifen), Sack beim Transport verloren (nächster Sack für denselben Platz). Wartezustände erscheinen als Zustandsmeldung.

## E/A-Belegung

Die Nummern sind Platzhalter und stehen in der DAT. Sie müssen zur E/A-Konfiguration in WorkVisual passen.

| Signal | DAT-Variable | Bedeutung |
| --- | --- | --- |
| `$IN[17]` | `nInSackDa` | Sack liegt am Anschlag der Aufnahme |
| `$IN[18]` | `nInPalBereit` | leere Palette in Position, Palettierung freigegeben |
| `$IN[19]` | `nInGabelAuf` | Endlage Gabel offen |
| `$IN[20]` | `nInGabelZu` | Endlage Gabel geschlossen |
| `$IN[21]` | `nInNiederOben` | Endlage Niederhalter oben |
| `$IN[22]` | `nInSackImGr` | Sensor Sack im Greifer |
| `$IN[23]` | `nInZyklEnde` | Zyklusende angewählt |
| `$OUT[17]` | `nOutGabelAuf` | Gabel öffnen |
| `$OUT[18]` | `nOutGabelZu` | Gabel schließen |
| `$OUT[19]` | `nOutNiederAb` | Niederhalter ab |
| `$OUT[20]` | `nOutSackEntn` | Sack entnommen: SPS speichert die steigende Flanke und fördert den nächsten Sack ein |
| `$OUT[21]` | `nOutPalVoll` | Palette voll: Palettenwechsel anfordern. Die SPS nimmt danach `$IN[18]` weg und setzt es wieder, sobald eine leere Palette steht. |

## Inbetriebnahme

1. `Palettierung.src` und `Palettierung.dat` nach `KRC:\R1\Program` kopieren (WorkVisual oder USB im Expertenmodus).
2. **Werkzeug 1 vermessen**: TCP in der Sackmitte, also Abstand Flansch bis Oberkante Gabelzinken minus 100 mm in Z. Orientierung A = B = C = 0. Lastdaten des Greifers eintragen.
3. **Lastdaten** `ldLeer` (Greifer) und `ldVoll` (Greifer mit Sack) in der DAT anpassen, am besten mit KUKA.LoadDataDetermination. Die Werte in der Datei sind Platzhalter.
4. **Basis 1 Palette** mit der 3-Punkt-Methode: Ursprung an der Ecke der Palettenoberkante, X entlang der 1200er Kante, Y entlang der 800er Kante.
5. **Basis 2 Aufnahme** mit der 3-Punkt-Methode: Ursprung an der Ecke des Sacks am Anschlag auf Rollenoberkante, X entlang der Sacklänge (entgegen der Förderrichtung), Y entlang der Sackbreite. Dann gelten `rPickX = 300`, `rPickY = 200`, `rPickZ = 100`.
6. **Orientierung prüfen**: Roboter mit Werkzeug 1 und Basis 0 verfahren, kartesische Istposition ablesen und B und C in `rOriB` und `rOriC` eintragen. Typisch sind B = 0 und C = 180.
7. **HOME prüfen**: `XHOME` muss außerhalb von Palettenplatz und Rollenbahn liegen, weil der Roboter dort den Palettenwechsel abwartet.
8. **E/A** in WorkVisual zuordnen und die Nummern in der DAT anpassen.
9. **Test** in T1 mit 10 % Override im Einzelsatz: zuerst ohne Sack, dann mit Säcken, erst dann T2 und Automatik.
10. **Feinabstimmung**: `rLagenH` verkleinern, wenn sich die Säcke setzen. `rAblageZ`, `rPickTief`, `rVorXY` und die Geschwindigkeiten nach Bedarf anpassen. Die Zähler `nLage` und `nSack` lassen sich in der Variablenanzeige setzen, um eine angefangene Palette fortzusetzen.

Für einen Offline-Test in OfficeLite oder KUKA.Sim ohne vermessene Basen `nBasePal = 0` und `nBasePick = 0` setzen. Dann gelten die Layout-Frames `fBasisPal` und `fBasisPick`, die dem Zellenlayout der Web-Simulation entsprechen (Roboterfuß im Weltursprung).

Sicherheitstechnik (Schutzzaun, Lichtgitter am Palettenplatz, Arbeitsraumüberwachung mit SafeOperation) ist nicht Teil dieses Programms und muss gesondert ausgelegt werden.

## Simulation

`simulation/index.html` im Browser öffnen. Für three.js und die Schriften wird eine Internetverbindung gebraucht.

- Die Simulation liest Maße, Lagenmuster, Offsets, Geschwindigkeiten und E/A-Nummern aus der eingebetteten `Palettierung.dat`. Im Reiter „Daten“ lässt sich die DAT ändern und übernehmen, etwa 3 Lagen oder ein anderes Muster.
- Der Ablauf bildet `Palettierung.src` Satz für Satz nach, einschließlich Vorlauf, Vorlaufstopp an E/A-Befehlen, Überschleifen (`C_PTP`, `C_DIS`) und Trigger. Im Reiter „Programm“ laufen Hauptlauf- und Vorlaufzeiger mit.
- Rollenbahn mit SPS-Handshake, Palettenwechsel, Sensoren und Meldungen sind nachgebildet. Mit „Sackzufuhr“ und „Zyklusende“ lassen sich Wartezustand und Programmende auslösen. „Satz“ fährt einen Satz weiter.
- Grenzen: Die Kinematik ist ein vereinfachtes Modell mit angenäherten Armlängen. Der Greifer ist schematisch, es gibt keine Kollisionsprüfung. Die angezeigte Taktzeit (im Modell rund 5,5 s je Sack) ist eine grobe Schätzung. Erreichbarkeit, Taktzeit und Störkonturen vor Ort mit KUKA.Sim oder WorkVisual prüfen.

Nach Änderungen an den KRL-Dateien die Simulation aktualisieren:

```
python3 simulation/embed_krl.py
```
