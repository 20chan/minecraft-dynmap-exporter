import os
import re
import time
from dotenv import load_dotenv

from rcon import Console
from prometheus_client import Metric, REGISTRY, start_http_server

load_dotenv()

rcon = Console(host=os.getenv('RCON_HOST'), password=os.getenv('RCON_PASSWORD'))

def tick():
  try:
    dynmap_tile_render_statistics = Metric('dynmap_tile_render_statistics', 'Tile Render Statistics reported by Dynmap', "counter")
    dynmap_chunk_loading_statistics_count = Metric('dynmap_chunk_loading_statistics_count', 'Chunk Loading Statistics reported by Dynmap', "counter")
    dynmap_chunk_loading_statistics_duration = Metric('dynmap_chunk_loading_statistics_duration', 'Chunk Loading Statistics reported by Dynmap', "counter")

    resp = rcon.command('dynmap stats').body

    dynmaptilerenderregex = re.compile("  (.*?): processed=(\d*), rendered=(\d*), updated=(\d*)")

    for dim, processed, rendered, updated in dynmaptilerenderregex.findall(resp):
      dynmap_tile_render_statistics.add_sample('dynmap_tile_render_statistics', value=processed, labels={'type': 'processed', 'file': dim})
      dynmap_tile_render_statistics.add_sample('dynmap_tile_render_statistics', value=rendered, labels={'type': 'rendered', 'file': dim})
      dynmap_tile_render_statistics.add_sample('dynmap_tile_render_statistics', value=updated, labels={'type': 'updated', 'file': dim})

      dynmapchunkloadingregex = re.compile("Chunks processed: (.*?): count=(\d*), (\d*.\d*)")
      for state, count, duration_per_chunk in dynmapchunkloadingregex.findall(resp):
          dynmap_chunk_loading_statistics_count.add_sample('dynmap_chunk_loading_statistics', value=count, labels={'type': state})
          dynmap_chunk_loading_statistics_duration.add_sample('dynmap_chunk_loading_duration', value=duration_per_chunk, labels={'type': state})

    return [dynmap_tile_render_statistics, dynmap_chunk_loading_statistics_count, dynmap_chunk_loading_statistics_duration]
  except Exception as e:
    print(e)
    return []


class Collector(object):
   def collect(self):
      metrics = tick()
      for metric in metrics:
        yield metric

if __name__ == '__main__':
  start_http_server(9200)
  REGISTRY.register(Collector())

  while True:
    time.sleep(1)