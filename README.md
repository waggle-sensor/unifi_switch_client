# Python Client for Unifi EdgeSwitch 8 150W
This client communicates with Unifi EdgeSwitch 8 150W to request user queries.

# Using Context Manager:
This can be used with Python context manager
```python
with UnifiSwitchClient(
        host='http://10.0.0.3',
        username='user',
        password='password') as client:
    print(client.get_mac_table())
    ...
```

# Using Class Instance:
```python
client = UnifiSwitchClient(
    host='http://10.0.0.3',
    username='user',
    password='password')
client.open()
print(client.get_mac_table())
client.close()
```

# Debugging
To debug, enable debug in logging in your code
```python
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(message)s',
    datefmt='%Y/%m/%d %H:%M:%S')
```