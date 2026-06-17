import sys
sys.path.insert(0, "apps/gestor_sistema")

from hikvision_sdk import HikvisionSDK, HikvisionSDKError, REMOTE_CONFIG_CALLBACK

sdk = HikvisionSDK(r"C:\HCNetSDK_runtime")
sdk.init()
user_id = sdk.login("192.168.1.13", 8000, "admin", "Dilan1105")
print(f"Login exitoso, user_id={user_id}")

comandos = {
    "NET_DVR_GET_FINGERPRINT": 2563,
    "NET_DVR_SET_FINGERPRINT": 2564,
    "NET_DVR_DEL_FINGERPRINT": 2565,
    "NET_DVR_CAPTURE_FINGERPRINT_INFO": 2504,
}

for nombre, codigo in comandos.items():
    handle = sdk.dll.NET_DVR_StartRemoteConfig(
        user_id, codigo, None, 0, REMOTE_CONFIG_CALLBACK(0), None
    )
    if handle == -1:
        err = sdk.dll.NET_DVR_GetLastError()
        print(f"FALLO {nombre} ({codigo}): codigo error {err}")
    else:
        print(f"OK {nombre} ({codigo}): canal abierto, handle={handle}")
        sdk.dll.NET_DVR_StopRemoteConfig(handle)

sdk.logout()
sdk.cleanup()