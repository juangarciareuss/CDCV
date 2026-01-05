from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.utils.text import slugify
from core.models import MicroCompetencia

# --- CONTROL DE ACCESO ---
# Solo el superusuario (tú) puede entrar aquí.
def es_superuser(user):
    return user.is_superuser

@user_passes_test(es_superuser)
def panel_mantenimiento(request):
    """
    Vista principal: Muestra el estado de salud de los datos.
    """
    # 1. Traemos todas las competencias
    competencias = MicroCompetencia.objects.all().order_by('id')
    
    # 2. Calculamos estadísticas rápidas
    total = competencias.count()
    sin_slug = competencias.filter(slug__isnull=True).count() + competencias.filter(slug='').count()
    
    context = {
        'competencias': competencias,
        'total': total,
        'sin_slug': sin_slug,
        'salud_sistema': 100 if sin_slug == 0 else int(((total - sin_slug) / total) * 100)
    }
    return render(request, 'maintenance/panel.html', context)

@user_passes_test(es_superuser)
def ejecutar_reparacion_slugs(request):
    """
    Acción: Repara los datos rotos.
    """
    reparados = 0
    errores = 0
    
    items = MicroCompetencia.objects.all()
    
    for item in items:
        # Si no tiene slug o está vacío
        if not item.slug:
            try:
                item.slug = slugify(item.nombre)
                item.save()
                reparados += 1
            except Exception as e:
                errores += 1
    
    if reparados > 0:
        messages.success(request, f"✅ Se repararon {reparados} competencias exitosamente.")
    elif errores > 0:
        messages.warning(request, f"⚠️ Hubo {errores} errores. Revisa que no haya nombres duplicados.")
    else:
        messages.info(request, "👍 Nada que reparar. Todo estaba perfecto.")
        
    return redirect('core:maintenance_panel')