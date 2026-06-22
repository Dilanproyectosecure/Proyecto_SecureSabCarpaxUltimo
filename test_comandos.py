import sys
sys.path.insert(0, "apps/gestor_sistema")


from hikvision_sdk import HikvisionSDK, HikvisionSDKError, REMOTE_CONFIG_CALLBACK
sdk = HikvisionSDK(r"C:\HCNetSDK_runtime")
sdk.init()
user_id = sdk.login("192.168.1.13", 8000, "admin", "Dilan1105")
print("Login exitoso, user_id=" + str(user_id))

comandos = {
    "GET_FINGERPRINT": 2563,
    "SET_FINGERPRINT": 2564,
    "DEL_FINGERPRINT": 2565,
    "CAPTURE_FINGERPRINT_INFO": 2504,
}

for nombre in comandos:
    codigo = comandos[nombre]
    handle = sdk.dll.NET_DVR_StartRemoteConfig(user_id, codigo, None, 0, REMOTE_CONFIG_CALLBACK(0), None)
    if handle == -1:
        err = sdk.dll.NET_DVR_GetLastError()
        print("FALLO " + nombre + " codigo error " + str(err))
    else:
        print("OK " + nombre + " handle=" + str(handle))
        sdk.dll.NET_DVR_StopRemoteConfig(handle)

sdk.logout()
sdk.cleanup()