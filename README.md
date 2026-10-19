# ThamesWatch Southend station discovery

Searches the Environment Agency Water Quality Explorer sampling-point API around 51.54 N, 0.71 E, within 20 km. Saves original JSON and a station CSV, preserving source identifiers. No pollutant measurements or RAG ratings are inferred.

## Run locally

```bash
pip install -r requirements.txt
python search_stations.py
```

## Run in GitHub Actions

Upload this folder's files into your GitHub repository. In the Actions tab, run **Find Southend monitoring stations**. Download the `southend-station-results` artifact from the completed run. The ZIP contains `output/southend_stations_20km.csv` and the raw API response. GitHub-hosted runners need network access to the Environment Agency endpoint.

## Important checks

The API has not been reachable from the environment that built this package, so live response shape and parameter semantics are not independently validated. If the workflow fails or returns no results, inspect the job logs and the current Environment Agency API documentation. The CSV includes only records whose coordinates parse and fall within the configured distance; review the raw JSON for excluded records. This script does not claim a site measures any of the requested pollutants.
