import requests
import platform
import psutil
import cpuinfo
import GPUtil

def get_location_from_ip(ip_address):
    """Get location information from IP address using ipapi.co"""
    try:
        response = requests.get(f'https://ipapi.co/{ip_address}/json/')
        if response.status_code == 200:
            data = response.json()
            return {
                'city': data.get('city', 'Unknown'),
                'region': data.get('region', 'Unknown'),
                'country': data.get('country_name', 'Unknown')
            }
    except Exception as e:
        print(f"Error getting location: {str(e)}")
    return {'city': 'Unknown', 'region': 'Unknown', 'country': 'Unknown'}

def get_device_info(request):
    """Get device information from request"""
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    return {
        'user_agent': user_agent,
        'platform': platform.system(),
        'browser': request.META.get('HTTP_USER_AGENT', '').split('/')[0]
    }

def get_system_info():
    """Get detailed system information"""
    try:
        # CPU Info
        cpu_info = cpuinfo.get_cpu_info()
        processor_info = cpu_info.get('brand_raw', 'Unknown')

        # GPU Info
        gpu_info = "No GPU detected"
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_info = gpus[0].name
        except:
            pass

        return {
            'processor_info': processor_info,
            'gpu_info': gpu_info,
            'os_info': f"{platform.system()} {platform.release()}",
            'bios_version': platform.version()
        }
    except Exception as e:
        print(f"Error getting system info: {str(e)}")
        return {
            'processor_info': 'Unknown',
            'gpu_info': 'Unknown',
            'os_info': 'Unknown',
            'bios_version': 'Unknown'
        } 