"""Wrap the built app fragment into a standalone, installable page.
Usage: python3 -I src/make_site.py <fragment.html> <index.html>
"""
import sys
frag = open(sys.argv[1]).read()
head = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#EEF1EF" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0E1412" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" href="icon-180.png">
<link rel="manifest" href="manifest.webmanifest">
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}[hidden]{display:none!important}img{max-width:100%}</style>
</head>
<body>
"""
# the artifact contract line is only meaningful on claude.ai
frag = frag.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
import re
m = re.search(r"<title>.*?</title>\n?", frag)
title = m.group(0) if m else "<title>Inflation Monitor</title>\n"
frag = frag.replace(m.group(0), "") if m else frag
head = head.replace("<meta charset=\"utf-8\">\n", "<meta charset=\"utf-8\">\n" + title)
import json, os, datetime
stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
# Self-update: the page compares its own build stamp with version.json (fetched past the cache)
# and reloads when a newer build is out. iOS home-screen apps otherwise keep stale copies.
updater = """<script>
(function(){var me=%s;function check(){fetch('version.json?t='+Date.now(),{cache:'no-store'}).then(function(r){return r.json()}).then(function(v){if(v&&v.build&&v.build!==me){location.replace(location.pathname+'?v='+v.build+location.hash)}}).catch(function(){})}
check();document.addEventListener('visibilitychange',function(){if(!document.hidden)check()});})();
</script>
""" % json.dumps(stamp)
open(sys.argv[2], "w").write(head + frag + "\n" + updater + "</body>\n</html>\n")
json.dump({"build": stamp}, open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[2])), "version.json"), "w"))
print("wrote", sys.argv[2])
