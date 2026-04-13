# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['server.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "socketio.threading_server",
        "socketio.asyncio_server",
        "engineio.threading_server",
        "engineio.asyncio_server",
        "flask_socketio",
        "flask_socketio.namespace",
        'socketio', 'socketio.admin', 'socketio.asgi', 'socketio.async_admin', 'socketio.async_aiopika_manager', 'socketio.async_client', 'socketio.async_manager', 'socketio.async_namespace', 'socketio.async_pubsub_manager', 'socketio.async_redis_manager', 'socketio.async_server', 'socketio.async_simple_client', 'socketio.base_client', 'socketio.base_manager', 'socketio.base_namespace', 'socketio.base_server', 'socketio.client', 'socketio.exceptions', 'socketio.kafka_manager', 'socketio.kombu_manager', 'socketio.manager', 'socketio.middleware', 'socketio.msgpack_packet', 'socketio.namespace', 'socketio.packet', 'socketio.pubsub_manager', 'socketio.redis_manager', 'socketio.server', 'socketio.simple_client', 'socketio.tornado', 'socketio.zmq_manager',
        'engineio', 'engineio.async_client', 'engineio.async_drivers', 'engineio.async_drivers._websocket_wsgi', 'engineio.async_drivers.aiohttp', 'engineio.async_drivers.asgi', 'engineio.async_drivers.eventlet', 'engineio.async_drivers.gevent', 'engineio.async_drivers.gevent_uwsgi', 'engineio.async_drivers.sanic', 'engineio.async_drivers.threading', 'engineio.async_drivers.tornado', 'engineio.async_server', 'engineio.async_socket', 'engineio.base_client', 'engineio.base_server', 'engineio.base_socket', 'engineio.client', 'engineio.exceptions', 'engineio.json', 'engineio.middleware', 'engineio.packet', 'engineio.payload', 'engineio.server', 'engineio.socket', 'engineio.static_files',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["eventlet",
        "gevent",
        "geventwebsocket"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='dictserver',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
