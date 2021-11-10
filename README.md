# Python Client for Unifi EdgeSwitch 8 150W
This client communicates with Unifi EdgeSwitch 8 150W to request user queries.

# Install
```bash
pip3 install https://github.com/waggle-sensor/unifi_switch_client/releases/download/0.0.2/unifi_switch_client-0.0.2-py3-none-any.whl
```

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