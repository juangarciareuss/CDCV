import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.sessions.models import Session

def nuclear_reset():
    print("☢️  INICIANDO LIMPIEZA NUCLEAR DE SESIONES...")
    
    # 1. Borramos todas las sesiones activas de usuarios
    # Esto te desconectará (log out), pero garantiza que se borre la lista vieja de 4 preguntas.
    count = Session.objects.count()
    Session.objects.all().delete()
    
    print(f"✅ Se eliminaron {count} sesiones activas.")
    print("   (La memoria del examen de Power BI ha sido borrada).")
    print("\n👉 INSTRUCCIÓN: Vuelve a loguearte en la web y entra al examen.")
    print("   Ahora el sistema estará OBLIGADO a usar el motor nuevo.")

if __name__ == "__main__":
    nuclear_reset()