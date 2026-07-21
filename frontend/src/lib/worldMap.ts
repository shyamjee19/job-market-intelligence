import { geoNaturalEarth1, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import type { Topology, GeometryCollection } from "topojson-specification";
// world-atlas ships plain JSON with no bundled types.
// eslint-disable-next-line @typescript-eslint/no-var-requires
import worldTopology from "world-atlas/countries-110m.json";

export const MAP_WIDTH = 960;
export const MAP_HEIGHT = 500;

// The backend's canonical country names (utils/geo.py) mostly match the
// topojson's `properties.name`, except these two.
const NAME_ALIASES: Record<string, string> = {
  "United States": "United States of America",
  "Czech Republic": "Czechia",
};

const topology = worldTopology as unknown as Topology;
const countries = feature(
  topology,
  topology.objects.countries as GeometryCollection,
) as unknown as GeoJSON.FeatureCollection;

const projection = geoNaturalEarth1().fitSize([MAP_WIDTH, MAP_HEIGHT], countries);
const pathGenerator = geoPath(projection);

export interface CountryPath {
  name: string;
  d: string;
}

export const COUNTRY_PATHS: CountryPath[] = countries.features
  .map((f) => ({
    // A few disputed territories (N. Cyprus, Somaliland, Kosovo) have a
    // real name but no numeric `id` in this atlas, all sharing `undefined`
    // - so `id` can't be a unique React key here. Every feature's `name`
    // is unique (verified against this dataset), and it's what coloring
    // and the tooltip already key off, so use it as the sole identifier.
    name: (f.properties as { name?: string }).name,
    d: pathGenerator(f) ?? "",
  }))
  .filter((c): c is CountryPath => Boolean(c.d && c.name));

export function backendNameToMapName(countryName: string): string {
  return NAME_ALIASES[countryName] ?? countryName;
}
