#!/bin/bash
set -e

echo "Waiting for MongoDB to accept connections..."
until mongosh --host mongo --eval "db.runCommand({ ping: 1 })" --quiet; do
  sleep 1
done

echo "Initiating replica set..."
mongosh --host mongo --eval '
  try {
    rs.initiate({ _id: "rs0", members: [{ _id: 0, host: "mongo:27017" }] });
    print("Replica set initiated");
  } catch (e) {
    if (e.codeName === "AlreadyInitialized") {
      print("Replica set already initialized");
    } else {
      throw e;
    }
  }
'
