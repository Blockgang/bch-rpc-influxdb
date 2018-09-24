import requests
from influxdb import InfluxDBClient
from datetime import datetime
import time

# influxdb connection info
influx_ip = "127.0.0.1"
influx_port = 8086
influx_db = "<influxdb-name>"
influx_user = "<influxdb-user>"
influx_pw = "<influxdb-password>"

#connection to influxdb
client = InfluxDBClient(influx_ip, influx_port, influx_user, influx_pw, influx_db)

#bitcoin rpc username + password
rpc_user = "<rpc-username>"
rpc_password = "<rpc-password>"
rpc_server = 'http://127.0.0.1:8332/'

def runner(method, params=None):

  headers = { 'content-type': 'text/plain;',}
  if params == None:
    data = '{"jsonrpc": "1.0", "id":"curltest", "method": "' + method + '"}'
  else:
    data = '{"jsonrpc": "1.0", "id":"curltest", "method": "' + method + '", "params": [' + params + ']}'
  print(data)
  r = requests.post(rpc_server, headers=headers, data=data, auth=(rpc_user, rpc_password))
  r.connection.close()
  req_data = r.json()['result']
  print(req_data)
  return req_data


#getmempoolinfo
getmempoolinfo = runner("getmempoolinfo")
mempool_tx_count = getmempoolinfo["size"]
mempool_bytes = getmempoolinfo["bytes"]
mempool_memory_usage = getmempoolinfo["usage"]

#getinfo
getinfo = runner("getinfo")
connections = getinfo["connections"]
block = getinfo["blocks"]
difficulty = getinfo["difficulty"]
sizelimit = getinfo["sizelimit"]
relayfee = getinfo["relayfee"]

#estimatefee - 6 blocks
estimate_fee = runner("estimatefee","6")

#datetime now()
datetime_now = datetime.utcnow().isoformat()

#networkhashps
networkhashps = runner("getnetworkhashps")

#mepool insert
json_body = [
      {
        "measurement": influx_db,
        "time": datetime_now,
        "tags": {
          "type": "mempool",
        },
        "fields": {
            "mempool_memory": int(mempool_memory_usage),
            "mempool_bytes": float(mempool_bytes),
            "mempool_tx_count": float(mempool_tx_count),
            "mempool_networkhashps": float(networkhashps),
            "mempool_estimate_fee": float(estimate_fee),
            "mempool_difficulty": float(difficulty)
        }
      }
  ]
client.write_points(json_body)

#nodeinfo insert
json_body = [
      {
        "measurement": influx_db,
        "time": datetime_now,
        "tags": {
          "type": "node",
        },
        "fields": {
            "node_connections": int(connections),
            "node_sizelimit": float(sizelimit),
            "node_relayfee": float(relayfee)
        }
      }
  ]

client.write_points(json_body)

height = block
startheight = height - 25 

for bestblock in range(startheight,height):

  blockhash = runner("getblockhash",str(bestblock))

  blockhash_string = '"' + str(blockhash) + '"'
  getblock = runner("getblock",blockhash_string)

  block_version = getblock["version"]
  block_tx_count = len(getblock["tx"])
  block_mediantime = getblock["mediantime"]
  block_difficulty = getblock["difficulty"]
  block_sizelimit = getblock["sizelimit"]
  block_size = getblock["size"]
  block_height = getblock["height"]

  block_mediantime = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime(block_mediantime))

  #block info insert
  json_body = [
      {
        "measurement": influx_db,
        "time": block_mediantime,
        "tags": {
          "type": "block",
        },
        "fields": {
            "block_height": block_height,
            "block_version": int(block_version),
            "block_tx_count": int(block_tx_count),
            "block_difficulty": float(block_difficulty),
            "block_sizelimit": float(block_sizelimit),
            "block_size": float(block_size)
        }
      }
    ]

  client.write_points(json_body)

#gettxoutsetinfo
gettxoutsetinfo = runner("gettxoutsetinfo")

disk_size = gettxoutsetinfo["disk_size"]
total_amount = gettxoutsetinfo["total_amount"]
transactions = gettxoutsetinfo["transactions"]
tx_out = gettxoutsetinfo["txouts"]

json_body = [
      {
        "measurement": influx_db,
        "time": datetime_now,
        "tags": {
          "type": "utxo",
        },
        "fields": {
            "utxo_disk_size": float(disk_size),
            "utxo_total_amount": int(total_amount),
            "utxo_transactions": float(transactions),
            "utxo_tx_out": int(tx_out)
        }
      }
  ]
client.write_points(json_body)
