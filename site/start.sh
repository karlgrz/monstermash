#!/bin/bash

cd /srv
uwsgi --http 0.0.0.0:8882 --module monstermash --callable app --enable-threads
