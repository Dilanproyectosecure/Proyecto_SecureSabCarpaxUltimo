import sys
sys.path.insert(0, "apps/gestor_sistema")

from hikvision_sdk import HikvisionSDK, HikvisionSDKError

sdk = HikvisionSDK(r"C:\HCNetSDK_runtime")
sdk.init()

try:
    user_id = sdk.login("192.168.1.13", 8000, "admin", "Dilan1105")
    print(f"Login exitoso, user_id={user_id}")
except HikvisionSDKError as e:
    print(f"Error de login: {e}")
    sys.exit()

resultado = sdk.enrolar_huella(
    finger_id=1,
    card_no="61",
    card_reader_no=1,
    finger_data=b"\x00" * 100,
)
print(resultado)

sdk.logout()
sdk.cleanup()
