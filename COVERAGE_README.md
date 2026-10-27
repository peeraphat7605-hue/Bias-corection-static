# Station coverage map

Open `map.html`. The original ranking calculations and embedded results are unchanged.

Coverage period: 1985-01-01 through 2014-12-31, 10,957 days per station. Include rainfall CSV station IDs from all years; stations appearing only after 2014 have 100% missing Historical data. Valid days require a nonnegative rainfall value and `observed` or `trace_as_zero` flag. Dash-as-zero, absent days and other flags are missing. Missing <=20% passes, including missing full years. Never fill values or modify rainfall CSVs.

Rebuild with Python, pandas and openpyxl:

```
python build_coverage.py --rain /path/to/Rainfall_Data --metadata /path/to/station_metadata.xlsx --out .
```

`coverage.json` records input SHA-256 hashes and the existing documented Tak Fa code correction. Ambiguous or absent coordinates are reported separately, never guessed. Red markers are clustered to avoid overlap; clicking clusters zooms or spiderfies, keeping real coordinates. Leaflet 1.9.4 and markercluster 1.5.3 load from unpkg; background tiles need internet (OpenStreetMap). Tables and CSV remain usable when map assets fail.

Validation: source station/date uniqueness; calendar length including leap years; independent row-count coverage reconciliation; missing interval lengths and yearly counts reconcile for every station. CSV exports include all stations and missing intervals. Raw rainfall values are not published by this feature.

