# iLvl Upgrade Odds

A desktop app built with Python and Tkinter that shows your chances of upgrading an item's level. Pick an item type and your current item level to see the **upgrade chance** and **failure chance** for one upgrade attempt.

---

## Features

* **Upgrade chance:** the chance to reach at least one item level higher (iLvl + 1 or more) from a single attempt.
* **Failure chance:** the chance the attempt fails and the item stays at its current iLvl. An attempt never lowers your item level.
* **Every possible result:** the odds of each outcome, from staying at the same level to jumping up to +5 levels.
* **Averages:** levels gained per attempt, attempts per +1 iLvl, and attempts until you get any upgrade.
* **Item type comparison:** Weapon, Armor and Accessory odds side by side at your current iLvl.
* **Failure curve chart:** failure chance across iLvl 51–90 for every item type. Click the chart to jump to a level.
* **Update from sheet:** pulls the latest odds from the source Google Sheet. The app has a built-in copy of the data, so it also works offline.

![iLvl Upgrade Odds](docs/screenshot.png)

---

## Download and run

Download `iLvl Upgrade Odds.exe` from the [Releases](../../releases) page and double-click it. You don't need to install Python.

## Run from source

Requires Python 3.10+ with Tkinter, which is included in the standard Windows installer.

```bash
python ilvl_odds.py
```

## Build the .exe

```bash
pip install pyinstaller
python -m PyInstaller --onefile --windowed --name "iLvl Upgrade Odds" ilvl_odds.py
```

The executable is written to `dist/`.

---

## Data

The odds come from the Upgrade Table tabs of the [upgrade odds spreadsheet](https://docs.google.com/spreadsheets/d/1vFb9oC9X8ZaV6It9wg1yczTTkggU54zAMFBs6FuPDZ8/edit), which reflects the latest patch. Each row of a table is a current iLvl, and each column is the chance of landing on a target iLvl. Jumps range from +0 to +5.

| Item type | Source tab |
|---|---|
| Weapon | Weapon Upgrade Table |
| Armor | Armor Upgrade Table |
| Accessory | Accessory Upgrade Table |

The tabs named "Data" (Weapons Data, Armor Data, Accessory Data) are not used.

How the values are calculated:

* Failure chance = P(+0)
* Upgrade chance = 1 − P(+0)
* Avg levels gained per attempt = Σ jump × P(jump)
* Avg attempts per +1 iLvl = 1 ÷ avg levels gained per attempt
* Avg attempts until any upgrade = 1 ÷ upgrade chance

Item level 90 is the cap, so an attempt at iLvl 90 always stays at 90. The app ignores the sheet's iLvl 90 row.
